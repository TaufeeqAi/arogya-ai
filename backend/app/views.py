"""Read models for the Home dashboard (UX-03), Care timeline (UX-17) and notification preferences (UX-19)."""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from sqlalchemy import select

from . import actions, memory
from .actions import TZ, fmt_dt
from .db import (Appointment, Approval, Doctor, Document, Medication, Patient, PharmacyOrder, RecordShare, Reminder,
                 session)

DEFAULT_NOTIFY = {
    "medication": True,          # medicine reminders
    "appointment": True,         # visit reminders
    "follow_up": True,           # doctor-advised follow-ups
    "refill": True,              # low-supply alerts
    "appointment_lead": ["1d", "2h"],
    "quiet_hours": {"enabled": True, "start": "22:00", "end": "07:00"},
    "caregiver_alerts": False,   # requires patient authorization (demo: off)
    "channel": "in_app",         # in_app | push (push needs the native notification service)
    "show_medicine_names": True, # privacy on lock screen / overlays
}


def notify_prefs(patient_id: str) -> dict:
    with session() as s:
        p = s.get(Patient, patient_id)
        saved = (p.preferences or {}).get("notifications", {}) if p else {}
    out = {**DEFAULT_NOTIFY, **saved}
    out["quiet_hours"] = {**DEFAULT_NOTIFY["quiet_hours"], **(saved.get("quiet_hours") or {})}
    return out


def save_notify_prefs(patient_id: str, patch: dict) -> dict:
    cur = notify_prefs(patient_id)
    for k, v in patch.items():
        if k not in DEFAULT_NOTIFY:
            continue
        if k == "quiet_hours" and isinstance(v, dict):
            cur["quiet_hours"] = {**cur["quiet_hours"], **{x: v[x] for x in ("enabled", "start", "end") if x in v}}
        else:
            cur[k] = v
    with session() as s:
        p = s.get(Patient, patient_id)
        p.preferences = {**(p.preferences or {}), "notifications": cur}
    return cur


def _hm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


def quiet_until(prefs: dict, now: datetime) -> datetime | None:
    """If `now` is inside quiet hours, return when they end (IST), else None."""
    q = prefs.get("quiet_hours") or {}
    if not q.get("enabled"):
        return None
    local = now.astimezone(TZ)
    start, end = _hm(q["start"]), _hm(q["end"])
    t = local.time()
    inside = (start <= t or t < end) if start > end else (start <= t < end)
    if not inside:
        return None
    end_dt = datetime.combine(local.date(), end, TZ)
    if end_dt <= local:
        end_dt += timedelta(days=1)
    return end_dt


def home(patient_id: str) -> dict:
    now = datetime.now(timezone.utc)
    local_today = datetime.now(TZ).date()
    day_start = datetime.combine(local_today, time(0), TZ)
    day_end = day_start + timedelta(days=1)
    with session() as s:
        p = s.get(Patient, patient_id)
        nxt = s.scalars(select(Appointment).where(Appointment.patient_id == patient_id, Appointment.status == "confirmed",
                                                  Appointment.start >= now).order_by(Appointment.start)).first()
        nxt_view = None
        if nxt:
            d = s.get(Doctor, nxt.doctor_id)
            nxt_view = {"doctor_name": d.name, "clinic": d.clinic, "area": d.area, "label": fmt_dt(nxt.start),
                        "booking_ref": nxt.booking_ref, "start": nxt.start.isoformat()}
        today = []
        for r in s.scalars(select(Reminder).where(Reminder.patient_id == patient_id, Reminder.kind.in_(("medication", "appointment")),
                                                  Reminder.due_at >= day_start, Reminder.due_at < day_end).order_by(Reminder.due_at)):
            today.append({"id": r.id, "kind": r.kind, "title": r.title, "time": r.due_at.astimezone(TZ).strftime("%I:%M %p"),
                          "status": r.status})
        pending = [{"approval_id": a.id, "action": a.action, "label": (a.payload or {}).get("label") or (a.payload or {}).get("item") or a.action}
                   for a in s.scalars(select(Approval).where(Approval.patient_id == patient_id, Approval.status == "pending"))]
        docs = [{"id": d.id, "title": d.title, "date": d.issued_on.isoformat(), "doc_type": d.doc_type, "status": d.status,
                 "trust_label": d.trust_label}
                for d in s.scalars(select(Document).where(Document.patient_id == patient_id).order_by(Document.created_at.desc()).limit(3))]
        low = [{"name": m.name, "strength": m.strength, "days": m.supply_left_days}
               for m in s.scalars(select(Medication).where(Medication.patient_id == patient_id)) if m.supply_left_days <= 5]
    from .tools import care_plan
    plan = [t for t in care_plan(patient_id) if t["status"] in ("open", "overdue")]
    cmp = memory.compare(patient_id)["comparisons"]
    key = [{"test_name": c["test_name"].split(" (")[0], "unit": c["unit"], "previous": c["previous"], "latest": c["latest"],
            "direction": c["direction"], "flag": c["latest_lab_flag"], "date": c["points"][-1]["observed_on"]}
           for c in cmp if c["test_code"] in ("HBA1C", "FBS", "LDL")]
    return {"patient": {"name": p.name, "first_name": p.name.split()[0]}, "next_appointment": nxt_view,
            "today_reminders": today, "pending_approvals": pending, "open_follow_ups": plan,
            "low_supply": low, "key_results": key, "recent_documents": docs}


def timeline(patient_id: str) -> list[dict]:
    ev: list[dict] = []
    with session() as s:
        for d in s.scalars(select(Document).where(Document.patient_id == patient_id)):
            ev.append({"ts": datetime.combine(d.issued_on, time(9), TZ).isoformat(), "type": "document",
                       "icon": {"lab_report": "🧪", "prescription": "💊", "consultation_note": "🩺"}.get(d.doc_type, "📄"),
                       "title": d.title, "detail": f"{d.source_name} · {d.trust_label.replace('_', ' ')}",
                       "document_id": d.id, "status": d.status})
        for a in s.scalars(select(Appointment).where(Appointment.patient_id == patient_id)):
            doc = s.get(Doctor, a.doctor_id)
            ev.append({"ts": a.start.isoformat(), "type": "appointment", "icon": "📅",
                       "title": f"Visit: {doc.name}", "detail": f"{doc.clinic} · ref {a.booking_ref}", "status": a.status})
            ev.append({"ts": a.created_at.isoformat(), "type": "action", "icon": "✅",
                       "title": f"Appointment booked with {doc.name}", "detail": f"Approved by you · verified ({a.booking_ref})",
                       "status": "done"})
        for r in s.scalars(select(Reminder).where(Reminder.patient_id == patient_id, Reminder.kind == "follow_up")):
            ev.append({"ts": r.due_at.isoformat(), "type": "follow_up", "icon": "📌", "title": r.title, "detail": r.body,
                       "status": r.status, "document_id": r.ref_id})
        for m in s.scalars(select(Medication).where(Medication.patient_id == patient_id)):
            ev.append({"ts": datetime.combine(m.start_date, time(10), TZ).isoformat(), "type": "medication", "icon": "💊",
                       "title": f"{m.name} {m.strength} started", "detail": m.frequency or "frequency not documented",
                       "status": m.status, "document_id": m.document_id})
        for sh in s.scalars(select(RecordShare).where(RecordShare.patient_id == patient_id)):
            d = s.get(Doctor, sh.doctor_id)
            ev.append({"ts": sh.created_at.isoformat(), "type": "sharing", "icon": "🔐",
                       "title": f"Records shared with {d.name if d else ''}",
                       "detail": f"{len(sh.document_ids)} document(s) · {sh.purpose or 'consultation'}", "status": sh.status})
        for o in s.scalars(select(PharmacyOrder).where(PharmacyOrder.patient_id == patient_id)):
            ev.append({"ts": o.created_at.isoformat(), "type": "medication", "icon": "📦", "title": f"Refill ordered: {o.item}",
                       "detail": f"{o.order_ref} · sandbox pharmacy", "status": o.status})
        for r in s.scalars(select(Reminder).where(Reminder.patient_id == patient_id, Reminder.kind == "medication",
                                                  Reminder.status.in_(("taken", "skipped")))):
            ev.append({"ts": r.due_at.isoformat(), "type": "medication", "icon": "✔️" if r.status == "taken" else "⏭️",
                       "title": f"{r.title}: {r.status} (self-reported)", "detail": "Patient-reported adherence", "status": r.status})
    now = datetime.now(timezone.utc)
    for e in ev:
        e["future"] = datetime.fromisoformat(e["ts"]) > now
        e["label"] = datetime.fromisoformat(e["ts"]).astimezone(TZ).strftime("%d %b %Y")
    return sorted(ev, key=lambda e: e["ts"], reverse=True)
