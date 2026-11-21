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
from .db import (Appointment, Approval, Doctor, Document, Medication, PharmacyOrder, RecordShare, Reminder, Slot,
                 session)
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
        superseded = []
        for a in s.scalars(select(Approval).where(Approval.patient_id == patient_id, Approval.action == action,
                                                  Approval.status == "pending")):
            a.status = "expired"
            superseded.append(a.id)
        a = Approval(patient_id=patient_id, session_id=session_id, action=action, payload=payload,
                     payload_hash=_hash(payload), expires_at=datetime.now(timezone.utc) + timedelta(minutes=10))
        s.add(a)
    for old_id in superseded:
        emit(patient_id, session_id, "approval_resolved", {"approval_id": old_id, "status": "expired"})
    ui(patient_id, session_id, "approval_card", {"approval_id": a.id, "action": action, "summary": summary,
                                                  "payload_hash": a.payload_hash[:12],
                                                  "expires_at": a.expires_at.isoformat()})
    activity(patient_id, session_id, "Approval requested", "waiting", summary.get("title", action), "create_approval")
    return a


def expire_pending(patient_id: str, session_id: str, action: str, reason: str) -> int:
    with session() as s:
        stale = list(s.scalars(select(Approval).where(Approval.patient_id == patient_id, Approval.action == action,
                                                      Approval.status == "pending")))
        for a in stale:
            a.status = "expired"
        ids = [a.id for a in stale]
    for i in ids:
        emit(patient_id, session_id, "approval_resolved", {"approval_id": i, "status": "expired"})
    if ids:
        activity(patient_id, session_id, "Previous proposal withdrawn", "done", reason, "expire_approval")
    return len(ids)


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
    activity(patient_id, session_id, "Action cancelled by patient", "cancelled", "", "reject_approval")
    emit(patient_id, session_id, "approval_resolved", {"approval_id": approval_id, "status": "rejected"})
    return {"status": "rejected"}


def execute(patient_id: str, session_id: str, approval_id: str, via: str, expected_hash: str = "") -> dict:
    """Validate the approval (owner, status, expiry, payload hash) then run the bound action exactly once."""
    expired = False
    with session() as s:
        a = s.get(Approval, approval_id)
        if not a or a.patient_id != patient_id:
            raise ActionError("APPROVAL_NOT_FOUND", "No such approval for this patient")
        if a.status == "executed":
            return {"status": "already_executed", **a.result}
        if a.status != "pending":
            raise ActionError("APPROVAL_NOT_PENDING", f"Approval is {a.status}")
        if _hash(a.payload) != a.payload_hash or (expected_hash and not a.payload_hash.startswith(expected_hash)):
            raise ActionError("APPROVAL_TAMPERED", "Approved details do not match the proposal")
        if a.expires_at < datetime.now(timezone.utc):
            a.status = "expired"  # committed when the session block exits
            expired = True
        else:
            a.status = "approved"
            a.decided_via = via
            action, payload = a.action, dict(a.payload)
    if expired:
        emit(patient_id, session_id, "approval_resolved", {"approval_id": approval_id, "status": "expired"})
        raise ActionError("APPROVAL_EXPIRED", "Approval expired; propose again")
    activity(patient_id, session_id, "Patient approved", "done", f"via {via}", "validate_approval")
    try:
        fn = {"book_appointment": _book, "share_records": _share, "medication_reminders": _med_reminders,
              "refill_order": _refill}[action]
        result = fn(patient_id, session_id, payload, approval_id)
        status = "executed"
    except ActionError as e:
        result, status = {"error": e.code, "message": e.message, **e.data}, "failed"
    except Exception as e:  # unexpected: outcome UNKNOWN until reconciled via the idempotency key; never retried blindly
        print("ACTION UNKNOWN OUTCOME", action, repr(e)[:200], flush=True)
        activity(patient_id, session_id, "Outcome unknown - needs reconciliation", "unknown", type(e).__name__, action)
        result, status = {"error": "UNKNOWN_OUTCOME",
                          "message": "The result could not be confirmed; nothing will be retried automatically."}, "unknown"
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
    n_rem = 0
    with session() as s:
        appt = s.get(Appointment, res["appointment_id"])
        appt.calendar_url = cal
        for task in s.scalars(select(Reminder).where(Reminder.patient_id == patient_id, Reminder.kind == "follow_up",
                                                     Reminder.status.in_(("open", "overdue")))):
            if "review" in task.title.lower():
                task.status = "booked"
                task.body = f"{task.body} | Booked: {p['doctor_name']}, {p['label']} (ref {res['booking_ref']})"
        from .views import notify_prefs
        leads = notify_prefs(patient_id).get("appointment_lead", ["1d", "2h"])
        for code, delta, label in (("1d", timedelta(days=1), "kal"), ("2h", timedelta(hours=2), "2 ghante mein")):
            if code not in leads:
                continue
            due = start - delta
            if due > datetime.now(timezone.utc):
                s.add(Reminder(patient_id=patient_id, kind="appointment", ref_id=appt.id,
                               title=f"Appointment {label}: {p['doctor_name']}",
                               body=f"{fmt_dt(start)} at {p['clinic']}. Ref {res['booking_ref']}", due_at=due))
                n_rem += 1
    activity(patient_id, session_id, f"Calendar link ready - {n_rem} reminders scheduled", "done",
             "Google Calendar + .ics", "create_calendar_event")
    result = {"booking_ref": res["booking_ref"], "appointment_id": res["appointment_id"], "status": "confirmed",
              "doctor_name": p["doctor_name"], "clinic": p["clinic"], "area": p["area"], "start": p["start"],
              "label": p["label"], "fee": p.get("fee"), "calendar_url": cal,
              "ics_url": f"/api/appointments/{res['appointment_id']}.ics", "reminders": n_rem}
    ui(patient_id, session_id, "booking_confirmation", result)
    return result


def _share(patient_id: str, session_id: str, p: dict, approval_id: str) -> dict:
    with session() as s:
        docs = [s.get(Document, d) for d in p["document_ids"]]
        if any(d is None or d.patient_id != patient_id for d in docs):
            raise ActionError("DOCUMENT_SCOPE", "Document not owned by patient")
        sh = RecordShare(patient_id=patient_id, doctor_id=p["doctor_id"], appointment_id=p.get("appointment_id", ""),
                         document_ids=p["document_ids"], purpose=p.get("purpose", "Upcoming consultation"),
                         expires_at=datetime.now(timezone.utc) + timedelta(days=7))
        s.add(sh)
    activity(patient_id, session_id, "Records shared with doctor (7-day access)", "done",
             ", ".join(d.title for d in docs), "share_records")
    result = {"share_id": sh.id, "doctor_name": p["doctor_name"], "documents": [d.title for d in docs],
              "purpose": p.get("purpose", "Upcoming consultation"), "expires_at": sh.expires_at.isoformat()}
    ui(patient_id, session_id, "share_confirmation", result)
    return result


def _med_reminders(patient_id: str, session_id: str, p: dict, approval_id: str) -> dict:
    with session() as s:
        m = s.get(Medication, p["medication_id"])
        if not m or m.patient_id != patient_id:
            raise ActionError("NOT_FOUND", "Medication not found")
        if m.status == "stopped":
            raise ActionError("STOPPED_MEDICATION", "This medicine was stopped by the doctor")
        if m.status not in ("verified", "reminders_active") or not m.times:
            raise ActionError("UNVERIFIED_INSTRUCTION", "Instructions incomplete; cannot schedule reminders")
        now_l = datetime.now(TZ)
        created = []
        days = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}
        recurrences = set()
        for t in m.times:
            wd = None
            if " " in t:  # weekly: "SUN 09:00"
                wd, t = t.split(" ", 1)
            hh, mm = map(int, t.split(":"))
            due = now_l.replace(hour=hh, minute=mm, second=0, microsecond=0)
            if wd:
                due += timedelta(days=(days[wd] - now_l.weekday()) % 7)
                if due <= now_l:
                    due += timedelta(days=7)
            elif due <= now_l:
                due += timedelta(days=1)
            rec = "weekly" if wd else "daily"
            recurrences.add(rec)
            s.add(Reminder(patient_id=patient_id, kind="medication", ref_id=m.id, recurrence=rec,
                           title=f"{m.name} {m.strength}", body=m.instructions, due_at=due))
            created.append(due.strftime("%a %I:%M %p") if wd else due.strftime("%I:%M %p"))
        m.status = "reminders_active"
        name = f"{m.name} {m.strength}"
    activity(patient_id, session_id, "Daily medication reminders scheduled", "done", f"{name} at {', '.join(created)}",
             "schedule_reminders")
    result = {"medication": name, "times": created, "recurrence": ", ".join(sorted(recurrences))}
    ui(patient_id, session_id, "medication_schedule", {"medications": medications_view(patient_id), "highlight": p["medication_id"]})
    return result


class SandboxPharmacy:
    """Stands in for a licensed partner pharmacy API (idempotent order + status lookup). No real sale or payment."""

    @staticmethod
    def place(patient_id: str, p: dict, idem_key: str) -> dict:
        with session() as s:
            ex = s.scalars(select(PharmacyOrder).where(PharmacyOrder.idempotency_key == idem_key)).first()
            if ex:
                return {"order_ref": ex.order_ref, "replayed": True}
            ref = "RX-" + "".join(random.choices(string.digits, k=6))
            s.add(PharmacyOrder(patient_id=patient_id, order_ref=ref, medication_id=p["medication_id"], item=p["item"],
                                quantity=p["quantity"], price_inr=p["price_inr"], idempotency_key=idem_key))
        return {"order_ref": ref, "replayed": False}

    @staticmethod
    def status(order_ref: str) -> str:
        with session() as s:
            o = s.scalars(select(PharmacyOrder).where(PharmacyOrder.order_ref == order_ref)).first()
            return o.status if o else "not_found"


def _refill(patient_id: str, session_id: str, p: dict, approval_id: str) -> dict:
    activity(patient_id, session_id, "Sending order to pharmacy (sandbox)", "running", p["pharmacy"], "place_order")
    res = SandboxPharmacy.place(patient_id, p, idem_key=f"approval:{approval_id}")
    st = SandboxPharmacy.status(res["order_ref"])
    if st == "not_found":
        raise ActionError("ORDER_UNVERIFIED", "Pharmacy did not confirm the order")
    activity(patient_id, session_id, "Pharmacy order verified", "done", f"{res['order_ref']} - {st.replace('_', ' ')}",
             "get_order_status")
    result = {"order_ref": res["order_ref"], "status": st, **p}
    ui(patient_id, session_id, "order_confirmation", result)
    return result


def cancel_order(patient_id: str, session_id: str, order_ref: str = "") -> dict:
    with session() as s:
        q = select(PharmacyOrder).where(PharmacyOrder.patient_id == patient_id, PharmacyOrder.status != "cancelled")
        if order_ref:
            q = q.where(PharmacyOrder.order_ref == order_ref)
        o = s.scalars(q.order_by(PharmacyOrder.created_at.desc())).first()
        if not o:
            return {"ok": False, "error": "NO_ORDER"}
        o.status = "cancelled"
        ref = o.order_ref
    activity(patient_id, session_id, "Pharmacy order cancelled", "done", f"{ref} (sandbox)", "cancel_order")
    return {"ok": True, "order_ref": ref, "status": SandboxPharmacy.status(ref)}


def list_shares(patient_id: str) -> list[dict]:
    now_ = datetime.now(timezone.utc)
    with session() as s:
        out = []
        q = select(RecordShare).where(RecordShare.patient_id == patient_id).order_by(RecordShare.created_at.desc())
        for sh in s.scalars(q):
            d = s.get(Doctor, sh.doctor_id)
            status = "expired" if sh.status == "active" and sh.expires_at < now_ else sh.status
            titles = [x.title for x in (s.get(Document, i) for i in sh.document_ids) if x]
            out.append({"share_id": sh.id, "doctor_name": d.name if d else sh.doctor_id, "documents": titles,
                        "purpose": sh.purpose, "status": status, "expires_at": sh.expires_at.isoformat(),
                        "label": fmt_dt(sh.expires_at)})
        return out


def revoke_share(patient_id: str, session_id: str, share_id: str = "") -> dict:
    with session() as s:
        q = select(RecordShare).where(RecordShare.patient_id == patient_id, RecordShare.status == "active")
        if share_id:
            q = q.where(RecordShare.id == share_id)
        sh = s.scalars(q.order_by(RecordShare.created_at.desc())).first()
        if not sh:
            return {"ok": False, "error": "NO_ACTIVE_SHARE"}
        sh.status = "revoked"
        d = s.get(Doctor, sh.doctor_id)
        share_id, name = sh.id, (d.name if d else "")
    activity(patient_id, session_id, "Record access revoked", "done", f"{name} can no longer view the shared records",
             "revoke_share")
    emit(patient_id, session_id, "document_updated", {"share_id": share_id, "status": "revoked"})
    return {"ok": True, "share_id": share_id, "doctor_name": name, "status": "revoked"}


def medications_view(patient_id: str) -> list[dict]:
    with session() as s:
        meds = list(s.scalars(select(Medication).where(Medication.patient_id == patient_id)))
        out = []
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        for m in meds:
            doc = s.get(Document, m.document_id)
            nxt = s.scalars(select(Reminder).where(Reminder.ref_id == m.id, Reminder.status == "scheduled")
                            .order_by(Reminder.due_at)).first()
            order = s.scalars(select(PharmacyOrder).where(PharmacyOrder.medication_id == m.id,
                                                          PharmacyOrder.status != "cancelled")
                              .order_by(PharmacyOrder.created_at.desc())).first()
            logs = list(s.scalars(select(Reminder).where(Reminder.ref_id == m.id, Reminder.due_at >= week_ago,
                                                         Reminder.status.in_(("taken", "skipped")))))
            out.append({"medication_id": m.id, "name": m.name, "strength": m.strength, "frequency": m.frequency,
                        "times": m.times, "instructions": m.instructions, "status": m.status,
                        "supply_left_days": m.supply_left_days,
                        "next_dose": fmt_dt(nxt.due_at) if nxt else None,
                        "refill_order": order.order_ref if order else None,
                        "adherence_7d": {"taken": sum(l.status == "taken" for l in logs),
                                         "skipped": sum(l.status == "skipped" for l in logs)} if logs else None,
                        "source": {"document_id": m.document_id, "title": doc.title, "trust_label": doc.trust_label}})
        rank = {"reminders_active": 0, "verified": 1, "needs_clarification": 2, "stopped": 3}
        out.sort(key=lambda x: rank.get(x["status"], 9))
        return out
