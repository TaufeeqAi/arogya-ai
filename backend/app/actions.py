"""Consequential actions: payload-bound approvals, idempotent execution, verification against the provider."""
from __future__ import annotations

import hashlib
import json
import random
import string
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo

import redis
from sqlalchemy import select

from .config import get_settings
from .db import Appointment, Approval, Doctor, Document, Medication, RecordShare, Reminder, Slot, session
from .events import activity, emit, ui

TZ = ZoneInfo(get_settings().timezone)
_r = redis.Redis.from_url(get_settings().redis_url, decode_responses=True)
CONFLICT_KEY = "aarogya:demo:conflict_next_booking"


class ActionError(Exception):
    def __init__(self, code: str, message: str, data: dict | None = None):
        super().__init__(message)
        self.code, self.message, self.data = code, message, data or {}


def _hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def fmt_dt(dt: datetime) -> str:
    return dt.astimezone(TZ).strftime("%a %d %b, %I:%M %p")


# ------------------------------------------------------------------ approvals
def create_approval(patient_id: str, session_id: str, action: str, payload: dict, summary: dict) -> Approval:
    with session() as s:
        # supersede older pending approvals of the same action
        for a in s.scalars(select(Approval).where(Approval.patient_id == patient_id, Approval.action == action,
                                                  Approval.status == "pending")):
            a.status = "expired"
        a = Approval(patient_id=patient_id, session_id=session_id, action=action, payload=payload,
                     payload_hash=_hash(payload), expires_at=datetime.now(timezone.utc) + timedelta(minutes=10))
        s.add(a)
    ui(patient_id, session_id, "approval_card", {"approval_id": a.id, "action": action, "summary": summary,
                                                  "expires_at": a.expires_at.isoformat()})
    activity(patient_id, session_id, "Approval requested", "waiting", summary.get("title", action), "create_approval")
    return a


def get_approval(patient_id: str, approval_id: str) -> Approval | None:
    with session() as s:
        a = s.get(Approval, approval_id)
        return a if a and a.patient_id == patient_id else None


def latest_pending(patient_id: str) -> Approval | None:
    with session() as s:
        return s.scalars(select(Approval).where(Approval.patient_id == patient_id, Approval.status == "pending")
                         .order_by(Approval.created_at.desc())).first()


def reject(patient_id: str, session_id: str, approval_id: str) -> dict:
    with session() as s:
        a = s.get(Approval, approval_id)
        if a and a.patient_id == patient_id and a.status == "pending":
            a.status = "rejected"
    activity(patient_id, session_id, "Action cancelled by patient", "done", "", "reject_approval")
    emit(patient_id, session_id, "approval_resolved", {"approval_id": approval_id, "status": "rejected"})
    return {"status": "rejected"}


def execute(patient_id: str, session_id: str, approval_id: str, via: str) -> dict:
    """Validate the approval (owner, status, expiry, payload hash) then run the bound action exactly once."""
    with session() as s:
        a = s.get(Approval, approval_id)
        if not a or a.patient_id != patient_id:
            raise ActionError("APPROVAL_NOT_FOUND", "No such approval for this patient")
        if a.status == "executed":
            return {"status": "already_executed", **a.result}
        if a.status != "pending":
            raise ActionError("APPROVAL_NOT_PENDING", f"Approval is {a.status}")
        if a.expires_at < datetime.now(timezone.utc):
            a.status = "expired"
            raise ActionError("APPROVAL_EXPIRED", "Approval expired; propose again")
        if _hash(a.payload) != a.payload_hash:
            raise ActionError("APPROVAL_TAMPERED", "Payload hash mismatch")
        a.status = "approved"
        a.decided_via = via
        action, payload = a.action, dict(a.payload)
    activity(patient_id, session_id, "Patient approved", "done", f"via {via}", "validate_approval")
    try:
        fn = {"book_appointment": _book, "share_records": _share, "medication_reminders": _med_reminders,
              "refill_order": _refill}[action]
        result = fn(patient_id, session_id, payload, approval_id)
        status = "executed"
    except ActionError as e:
        result, status = {"error": e.code, "message": e.message, **e.data}, "failed"
    with session() as s:
        a = s.get(Approval, approval_id)
        a.status, a.result = status, json.loads(json.dumps(result, default=str))
    emit(patient_id, session_id, "approval_resolved", {"approval_id": approval_id, "status": status})
    if status == "failed":
        raise ActionError(result["error"], result["message"], {k: v for k, v in result.items() if k not in ("error", "message")})
    return result


# ------------------------------------------------------------------ simulated clinic booking provider
class ClinicBookingProvider:
    """Stands in for an external clinic scheduling API (idempotent create + status lookup)."""

    @staticmethod
    def book(patient_id: str, slot_id: str, idem_key: str) -> dict:
        with session() as s:
            existing = s.scalars(select(Appointment).where(Appointment.idempotency_key == idem_key)).first()
            if existing:
                return {"booking_ref": existing.booking_ref, "appointment_id": existing.id, "replayed": True}
            slot = s.get(Slot, slot_id, with_for_update=True)
            if not slot or slot.status != "open":
                raise ActionError("SLOT_UNAVAILABLE", "Slot no longer available")
            slot.status = "booked"
            ref = "APX-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            appt = Appointment(patient_id=patient_id, doctor_id=slot.doctor_id, slot_id=slot.id, start=slot.start,
                               booking_ref=ref, idempotency_key=idem_key)
            s.add(appt)
        return {"booking_ref": ref, "appointment_id": appt.id, "replayed": False}

    @staticmethod
    def status(booking_ref: str) -> dict:
        with session() as s:
            appt = s.scalars(select(Appointment).where(Appointment.booking_ref == booking_ref)).first()
            return {"booking_ref": booking_ref, "status": appt.status if appt else "not_found"}


def alternatives(doctor_id: str, after: datetime, n: int = 3) -> list[dict]:
    with session() as s:
        d = s.get(Doctor, doctor_id)
        slots = s.scalars(select(Slot).where(Slot.doctor_id == doctor_id, Slot.status == "open",
                                             Slot.start >= after).order_by(Slot.start).limit(n))
        return [{"slot_id": x.id, "doctor_id": doctor_id, "doctor_name": d.name, "start": x.start.isoformat(),
                 "label": fmt_dt(x.start)} for x in slots]


def calendar_link(title: str, start: datetime, minutes: int, details: str, location: str) -> str:
    f = "%Y%m%dT%H%M%SZ"
    s, e = start.astimezone(timezone.utc), start.astimezone(timezone.utc) + timedelta(minutes=minutes)
    return ("https://calendar.google.com/calendar/render?action=TEMPLATE"
            f"&text={quote(title)}&dates={s.strftime(f)}/{e.strftime(f)}&details={quote(details)}&location={quote(location)}")


def _book(patient_id: str, session_id: str, p: dict, approval_id: str) -> dict:
    # 1. revalidate exact slot after approval
    activity(patient_id, session_id, "Re-checking slot availability", "running", p["label"], "revalidate_slot")
    with session() as s:
        slot = s.get(Slot, p["slot_id"])
        doc = s.get(Doctor, p["doctor_id"])
        if _r.getdel(CONFLICT_KEY) and slot and slot.status == "open":
            slot.status = "booked"  # demo: another patient took it between proposal and approval
        ok = slot and slot.status == "open" and slot.doctor_id == p["doctor_id"]
        slot_start = slot.start if slot else datetime.now(timezone.utc)
    if not ok:
        alts = alternatives(p["doctor_id"], slot_start)
        activity(patient_id, session_id, "Slot was just taken by someone else", "failed", p["label"], "revalidate_slot")
        if alts:
            ui(patient_id, session_id, "doctor_slots", {"doctor": {"id": doc.id, "name": doc.name, "clinic": doc.clinic,
                                                                  "area": doc.area, "fee": doc.fee},
                                                       "slots": alts, "note": "Previous slot is no longer available"})
        raise ActionError("SLOT_UNAVAILABLE", "The approved slot was taken before booking; nothing was booked.",
                          {"alternatives": alts})
    activity(patient_id, session_id, "Slot still available", "done", p["label"], "revalidate_slot")

    # 2. idempotent booking with provider
    res = ClinicBookingProvider.book(patient_id, p["slot_id"], idem_key=f"approval:{approval_id}")
    activity(patient_id, session_id, "Booked with clinic system", "done", f"Ref {res['booking_ref']}", "book_appointment")

    # 3. verify against provider before claiming success
    st = ClinicBookingProvider.status(res["booking_ref"])
    if st["status"] != "confirmed":
        raise ActionError("BOOKING_UNVERIFIED", "Clinic did not confirm the booking", st)
    activity(patient_id, session_id, "Booking verified", "done", f"{res['booking_ref']} = confirmed", "get_booking_status")

    # 4. calendar + reminders (separate effects; failure here doesn't undo the booking)
    start = datetime.fromisoformat(p["start"])
    cal = calendar_link(f"Doctor visit: {p['doctor_name']}", start, 30,
                        f"Booking ref {res['booking_ref']}. Carry latest reports. (Aarogya)", f"{p['clinic']}, {p['area']}")
    with session() as s:
        appt = s.get(Appointment, res["appointment_id"])
        appt.calendar_url = cal
        for delta, label in ((timedelta(days=1), "kal"), (timedelta(hours=2), "2 ghante mein")):
            due = start - delta
            if due > datetime.now(timezone.utc):
                s.add(Reminder(patient_id=patient_id, kind="appointment", ref_id=appt.id,
                               title=f"Appointment {label}: {p['doctor_name']}",
                               body=f"{fmt_dt(start)} at {p['clinic']}. Ref {res['booking_ref']}", due_at=due))
    activity(patient_id, session_id, "Calendar event + 2 reminders created", "done", "", "create_calendar_event")
    result = {"booking_ref": res["booking_ref"], "appointment_id": res["appointment_id"], "status": "confirmed",
              "doctor_name": p["doctor_name"], "clinic": p["clinic"], "area": p["area"], "start": p["start"],
              "label": p["label"], "fee": p.get("fee"), "calendar_url": cal,
              "ics_url": f"/api/appointments/{res['appointment_id']}.ics"}
    ui(patient_id, session_id, "booking_confirmation", result)
    return result


def _share(patient_id: str, session_id: str, p: dict, approval_id: str) -> dict:
    with session() as s:
        docs = [s.get(Document, d) for d in p["document_ids"]]
        if any(d is None or d.patient_id != patient_id for d in docs):
            raise ActionError("DOCUMENT_SCOPE", "Document not owned by patient")
        sh = RecordShare(patient_id=patient_id, doctor_id=p["doctor_id"], appointment_id=p.get("appointment_id", ""),
                         document_ids=p["document_ids"], expires_at=datetime.now(timezone.utc) + timedelta(days=7))
        s.add(sh)
    activity(patient_id, session_id, "Records shared with doctor (7-day access)", "done",
             ", ".join(d.title for d in docs), "share_records")
    result = {"share_id": sh.id, "doctor_name": p["doctor_name"], "documents": [d.title for d in docs],
              "expires_at": sh.expires_at.isoformat()}
    ui(patient_id, session_id, "share_confirmation", result)
    return result


def _med_reminders(patient_id: str, session_id: str, p: dict, approval_id: str) -> dict:
    with session() as s:
        m = s.get(Medication, p["medication_id"])
        if not m or m.patient_id != patient_id:
            raise ActionError("NOT_FOUND", "Medication not found")
        if m.status not in ("verified", "reminders_active") or not m.times:
            raise ActionError("UNVERIFIED_INSTRUCTION", "Instructions incomplete; cannot schedule reminders")
        now_l = datetime.now(TZ)
        created = []
        for t in m.times:
            hh, mm = map(int, t.split(":"))
            due = now_l.replace(hour=hh, minute=mm, second=0, microsecond=0)
            if due <= now_l:
                due += timedelta(days=1)
            s.add(Reminder(patient_id=patient_id, kind="medication", ref_id=m.id, recurrence="daily",
                           title=f"{m.name} {m.strength}", body=m.instructions, due_at=due))
            created.append(due.strftime("%I:%M %p"))
        m.status = "reminders_active"
        name = f"{m.name} {m.strength}"
    activity(patient_id, session_id, "Daily medication reminders scheduled", "done", f"{name} at {', '.join(created)}",
             "schedule_reminders")
    result = {"medication": name, "times": created, "recurrence": "daily"}
    ui(patient_id, session_id, "medication_schedule", {"medications": medications_view(patient_id), "highlight": p["medication_id"]})
    return result


def _refill(patient_id: str, session_id: str, p: dict, approval_id: str) -> dict:
    activity(patient_id, session_id, "Sending order to pharmacy (sandbox)", "running", p["pharmacy"], "place_order")
    ref = "RX-" + "".join(random.choices(string.digits, k=6))
    activity(patient_id, session_id, "Pharmacy confirmed order", "done", f"{ref} · pharmacist verification pending",
             "get_order_status")
    result = {"order_ref": ref, "status": "confirmed_pending_pharmacist_check", **p}
    ui(patient_id, session_id, "order_confirmation", result)
    return result


def medications_view(patient_id: str) -> list[dict]:
    with session() as s:
        meds = list(s.scalars(select(Medication).where(Medication.patient_id == patient_id)))
        out = []
        for m in meds:
            doc = s.get(Document, m.document_id)
            out.append({"medication_id": m.id, "name": m.name, "strength": m.strength, "frequency": m.frequency,
                        "times": m.times, "instructions": m.instructions, "status": m.status,
                        "supply_left_days": m.supply_left_days,
                        "source": {"document_id": m.document_id, "title": doc.title, "trust_label": doc.trust_label}})
        return out
