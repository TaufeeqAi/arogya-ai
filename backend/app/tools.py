"""Typed tools exposed to the LangGraph agent. Patient scope comes from server config, never from the model."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from sqlalchemy import select

from . import actions, memory, safety
from .actions import TZ, ActionError, fmt_dt
from .db import Appointment, Doctor, Document, Medication, Patient, Slot, session
from .events import activity, ui


def _ctx(config: RunnableConfig) -> tuple[str, str]:
    c = config.get("configurable", {})
    return c["patient_id"], c.get("session_id", "")


def _err(e: ActionError) -> dict:
    return {"ok": False, "error": e.code, "message": e.message, **e.data}


@tool
def get_patient_overview(config: RunnableConfig) -> dict:
    """Get the patient's profile, known conditions, allergies, preferences, documents on record, active
    medications and upcoming appointments. Call this first when you need context about the patient."""
    pid, sid = _ctx(config)
    with session() as s:
        p = s.get(Patient, pid)
        docs = list(s.scalars(select(Document).where(Document.patient_id == pid).order_by(Document.issued_on.desc())))
        appts = list(s.scalars(select(Appointment).where(Appointment.patient_id == pid, Appointment.status == "confirmed")))
        appt_view = []
        for a in appts:
            d = s.get(Doctor, a.doctor_id)
            appt_view.append({"appointment_id": a.id, "doctor": d.name, "when": fmt_dt(a.start), "ref": a.booking_ref})
    activity(pid, sid, "Loaded health profile", "done", f"{len(docs)} documents on record", "get_patient_overview")
    return {"name": p.name, "age": p.age, "sex": p.sex, "location": f"{p.area}, {p.city}", "conditions": p.conditions,
            "allergies": p.allergies, "preferences": p.preferences,
            "documents": [{"document_id": d.id, "title": d.title, "type": d.doc_type, "date": d.issued_on.isoformat(),
                           "trust": d.trust_label} for d in docs],
            "medications": [{k: m[k] for k in ("medication_id", "name", "strength", "frequency", "status")}
                            for m in actions.medications_view(pid)],
            "upcoming_appointments": appt_view}


@tool
def get_lab_report(config: RunnableConfig, document_id: str = "latest") -> dict:
    """Get every measured value from one lab report with units, the lab's printed reference range, the lab's
    flag and source reference. Use document_id='latest' for the most recent report, 'previous' for the one
    before it, or an explicit document_id. Shows the report card on the patient's screen."""
    pid, sid = _ctx(config)
    labs = memory.lab_documents(pid)
    if not labs:
        return {"ok": False, "message": "No lab reports on record"}
    if document_id in ("latest", "previous"):
        idx = 0 if document_id == "latest" or len(labs) < 2 else 1
        document_id = labs[idx].id
    doc, obs = memory.report_observations(pid, document_id)
    if not doc:
        return {"ok": False, "message": "Report not found for this patient"}
    activity(pid, sid, "Retrieved lab report", "done", f"{doc.title} · {len(obs)} values", "get_lab_observations")
    flagged = [o for o in obs if o["lab_flag"] != "within lab range"]
    ui(pid, sid, "lab_summary", {"document": {"id": doc.id, "title": doc.title, "date": doc.issued_on.isoformat(),
                                              "source_name": doc.source_name, "trust_label": doc.trust_label},
                                 "observations": obs, "flagged_count": len(flagged)})
    return {"ok": True, "document": {"id": doc.id, "title": doc.title, "date": doc.issued_on.isoformat(),
                                     "lab": doc.source_name}, "observations": obs,
            "outside_lab_range": [f"{o['test_name']}: {o['value']} {o['unit']} (lab range {o['reference_range']})"
                                  for o in flagged]}


@tool
def compare_lab_history(config: RunnableConfig, test_codes: list[str] | None = None) -> dict:
    """Deterministically compare the latest lab values with the previous report for the same tests.
    Optional test_codes filter, e.g. ["HBA1C","LDL"]. Known codes: HBA1C, FBS, CHOL, LDL, HDL, TG, CREAT, HB,
    VITD, TSH. Returns numeric change only (no clinical interpretation) and shows a comparison chart."""
    pid, sid = _ctx(config)
    res = memory.compare(pid, [c.upper() for c in test_codes] if test_codes else None)
    n = len(res["comparisons"])
    activity(pid, sid, "Compared with previous report", "done",
             f"{n} matching tests · {len(res['not_comparable'])} not comparable", "compare_lab_observations")
    ui(pid, sid, "comparison_chart", res)
    slim = [{k: c[k] for k in ("test_name", "unit", "previous", "latest", "change", "change_pct", "direction",
                                "reference_range", "latest_lab_flag")} | {"history": [f"{p['observed_on']}: {p['value']}" for p in c["points"]]}
            for c in res["comparisons"]]
    return {"ok": True, "method": res["method"], "comparisons": slim, "not_comparable": res["not_comparable"]}


@tool
def search_health_records(config: RunnableConfig, query: str) -> dict:
    """Semantic search over the patient's own documents (consultation notes, prescriptions, reports) for
    narrative facts such as doctor advice, follow-up instructions, complaints or allergies. Query in English."""
    pid, sid = _ctx(config)
    hits = memory.semantic_search(pid, query)
    activity(pid, sid, "Searched health memory", "done", f"\"{query}\" · {len(hits)} passages", "search_health_records")
    return {"ok": True, "results": [{"document_id": h["document_id"], "title": h["title"],
                                     "date": h.get("issued_on"), "text": h["text"]} for h in hits]}


@tool
def search_doctors(config: RunnableConfig, specialty: str = "", language: str = "", area: str = "") -> dict:
    """Search the connected provider directory. specialty e.g. 'General Physician' or 'Endocrinologist'
    (diabetes specialist). Optional language (e.g. 'Hindi') and area filters. Empty specialty returns all."""
    pid, sid = _ctx(config)
    with session() as s:
        docs = list(s.scalars(select(Doctor)))
    def match(d: Doctor) -> bool:
        if specialty and specialty.lower().split()[0][:5] not in d.specialty.lower():
            return False
        if language and language.lower() not in [l.lower() for l in d.languages]:
            return False
        if area and area.lower() not in d.area.lower():
            return False
        return True
    found = [d for d in docs if match(d)] or [d for d in docs if not specialty or specialty.lower()[:5] in d.specialty.lower()] or docs
    activity(pid, sid, "Searched doctor directory", "done", f"{len(found)} doctors match", "search_doctors")
    return {"ok": True, "doctors": [{"doctor_id": d.id, "name": d.name, "specialty": d.specialty, "clinic": d.clinic,
                                     "area": d.area, "languages": d.languages, "fee_inr": d.fee, "rating": d.rating,
                                     "experience_years": d.experience_years} for d in found]}


@tool
def check_slots(config: RunnableConfig, doctor_id: str, date_iso: str, part_of_day: str = "any") -> dict:
    """Get currently open appointment slots for one doctor on a date (YYYY-MM-DD).
    part_of_day: morning (before 1 PM) | afternoon | evening | any. Shows slot cards on screen."""
    pid, sid = _ctx(config)
    actions.expire_pending(pid, sid, "book_appointment", "patient is looking at other slots")
    try:
        day = date.fromisoformat(date_iso)
    except ValueError:
        return {"ok": False, "error": "BAD_DATE", "message": "Use YYYY-MM-DD"}
    lo, hi = {"morning": (time(0), time(13)), "afternoon": (time(13), time(17)),
              "evening": (time(17), time(23, 59))}.get(part_of_day, (time(0), time(23, 59)))
    now = datetime.now(TZ)
    with session() as s:
        d = s.get(Doctor, doctor_id)
        if not d:
            return {"ok": False, "error": "UNKNOWN_DOCTOR"}
        slots = list(s.scalars(select(Slot).where(
            Slot.doctor_id == doctor_id, Slot.status == "open",
            Slot.start >= datetime.combine(day, lo, TZ), Slot.start <= datetime.combine(day, hi, TZ),
            Slot.start > now).order_by(Slot.start)))
    view = [{"slot_id": x.id, "doctor_id": d.id, "doctor_name": d.name, "start": x.start.isoformat(),
             "label": fmt_dt(x.start)} for x in slots]
    activity(pid, sid, "Checked live availability", "done", f"{d.name} · {day.strftime('%a %d %b')} · {len(view)} open",
             "check_appointment_slots")
    doctor = {"id": d.id, "name": d.name, "clinic": d.clinic, "area": d.area, "fee": d.fee, "specialty": d.specialty}
    if view:
        ui(pid, sid, "doctor_slots", {"doctor": doctor, "slots": view})
        return {"ok": True, "doctor": doctor, "slots": view}
    nxt = actions.alternatives(doctor_id, datetime.combine(day, lo, TZ))
    if nxt:
        ui(pid, sid, "doctor_slots", {"doctor": doctor, "slots": nxt, "note": "No slots in requested window; next available"})
    return {"ok": True, "doctor": doctor, "slots": [], "next_available": nxt}


@tool
def propose_appointment(config: RunnableConfig, slot_id: str) -> dict:
    """Prepare a booking for a specific slot and ask the patient to approve it. This does NOT book.
    Shows an approval card. After calling, ask the patient to confirm."""
    pid, sid = _ctx(config)
    with session() as s:
        sl = s.get(Slot, slot_id)
        if not sl or sl.status != "open":
            return {"ok": False, "error": "SLOT_UNAVAILABLE", "message": "That slot is not open"}
        d = s.get(Doctor, sl.doctor_id)
        payload = {"slot_id": sl.id, "doctor_id": d.id, "doctor_name": d.name, "clinic": d.clinic, "area": d.area,
                   "start": sl.start.isoformat(), "label": fmt_dt(sl.start), "fee": d.fee, "mode": sl.mode}
    a = actions.create_approval(pid, sid, "book_appointment", payload, {
        "title": f"Book {d.name}", "lines": [f"{d.clinic}, {d.area}", payload["label"], f"Consultation fee ₹{d.fee}",
                                             "In-person visit"]})
    return {"ok": True, "approval_id": a.id, "status": "awaiting_patient_approval", "proposal": payload}


@tool
def confirm_action(config: RunnableConfig, approval_id: str = "") -> dict:
    """Execute a pending approved action ONLY after the patient has explicitly said yes (e.g. 'haan', 'yes',
    'book kar do') to that exact proposal in their latest message. Leave approval_id empty to use the latest
    pending approval. If it returns NO_PENDING_APPROVAL, call propose_appointment for the slot the patient
    chose and ask them to confirm. Returns verified outcome or an error with alternatives."""
    pid, sid = _ctx(config)
    c = config.get("configurable", {})
    a = actions.latest_pending(pid) if not approval_id else actions.get_approval(pid, approval_id)
    if not a:
        return {"ok": False, "error": "NO_PENDING_APPROVAL"}
    approval_id = a.id
    # Deterministic human-in-the-loop gate: the patient must have SEEN the proposal (created in an earlier
    # turn) and must say an explicit yes in THIS turn. The LLM cannot bypass this.
    turn_started = c.get("turn_started")
    if turn_started and a.created_at.isoformat() >= turn_started:
        return {"ok": False, "error": "APPROVAL_NOT_YET_SHOWN",
                "message": "Proposal was just created. Ask the patient to confirm it first; do not execute yet."}
    if c.get("user_text") is not None and not safety.is_affirmative(c["user_text"]):
        return {"ok": False, "error": "NO_EXPLICIT_CONSENT",
                "message": "Patient's latest message is not an explicit yes. Ask them to confirm."}
    try:
        return {"ok": True, **actions.execute(pid, sid, approval_id, via="voice confirmation")}
    except ActionError as e:
        return _err(e)


@tool
def cancel_pending_action(config: RunnableConfig, approval_id: str = "") -> dict:
    """Cancel the pending proposal when the patient says no, rejects the offered slot/time, or changes their mind.
    ALWAYS call this before searching alternatives after the patient rejects a proposal."""
    pid, sid = _ctx(config)
    a = actions.latest_pending(pid) if not approval_id else None
    return actions.reject(pid, sid, approval_id or (a.id if a else ""))


@tool
def propose_record_share(config: RunnableConfig, appointment_id: str, document_ids: list[str]) -> dict:
    """Prepare sharing specific documents with the doctor of a booked appointment. Requires separate patient
    consent (approval card). Does not share until confirm_action after the patient says yes."""
    pid, sid = _ctx(config)
    with session() as s:
        appt = s.get(Appointment, appointment_id)
        if not appt or appt.patient_id != pid:
            return {"ok": False, "error": "APPOINTMENT_NOT_FOUND"}
        d = s.get(Doctor, appt.doctor_id)
        docs = [s.get(Document, x) for x in document_ids]
        if any(x is None or x.patient_id != pid for x in docs):
            return {"ok": False, "error": "DOCUMENT_NOT_FOUND"}
    payload = {"doctor_id": d.id, "doctor_name": d.name, "appointment_id": appointment_id, "document_ids": document_ids}
    a = actions.create_approval(pid, sid, "share_records", payload, {
        "title": f"Share records with {d.name}", "lines": [x.title for x in docs] + ["Access expires in 7 days"]})
    return {"ok": True, "approval_id": a.id, "status": "awaiting_patient_consent"}


@tool
def get_medications(config: RunnableConfig) -> dict:
    """List the patient's recorded medicines with instructions exactly as documented, verification status,
    remaining supply and source prescription. Shows the medication card."""
    pid, sid = _ctx(config)
    meds = actions.medications_view(pid)
    activity(pid, sid, "Retrieved medication record", "done", f"{len(meds)} medicines", "get_medications")
    ui(pid, sid, "medication_schedule", {"medications": meds})
    return {"ok": True, "medications": meds}


@tool
def propose_medication_reminders(config: RunnableConfig, medication_id: str) -> dict:
    """Prepare daily reminders for a medicine using ONLY the verified prescription times. Refuses if the
    instructions are incomplete. Requires patient approval (confirm_action)."""
    pid, sid = _ctx(config)
    with session() as s:
        m = s.get(Medication, medication_id)
        if not m or m.patient_id != pid:
            return {"ok": False, "error": "NOT_FOUND"}
        if m.status == "reminders_active":
            return {"ok": True, "status": "already_active", "medication": f"{m.name} {m.strength}", "times": m.times,
                    "message": "Daily reminders are already active for this medicine; nothing to change."}
        if m.status == "needs_clarification" or not m.times:
            activity(pid, sid, "Blocked: prescription instruction incomplete", "failed", f"{m.name} {m.strength}",
                     "validate_medication")
            return {"ok": False, "error": "UNVERIFIED_INSTRUCTION",
                    "message": f"{m.name}: '{m.instructions}'. Cannot create reminders; ask the prescribing doctor or pharmacist."}
        payload = {"medication_id": m.id, "times": m.times}
        lines = [f"{m.name} {m.strength} · {m.frequency}", f"Daily at {', '.join(m.times)}", m.instructions,
                 "Source: prescription on record"]
    a = actions.create_approval(pid, sid, "medication_reminders", payload, {"title": "Set medicine reminders", "lines": lines})
    return {"ok": True, "approval_id": a.id, "status": "awaiting_patient_approval"}


@tool
def propose_refill(config: RunnableConfig, medication_id: str) -> dict:
    """Prepare a refill order for a VERIFIED medicine from the sandbox partner pharmacy (same strength and
    instructions as prescribed). Shows a quote card; requires approval via confirm_action."""
    pid, sid = _ctx(config)
    with session() as s:
        m = s.get(Medication, medication_id)
        if not m or m.patient_id != pid:
            return {"ok": False, "error": "NOT_FOUND"}
        if m.status == "needs_clarification":
            return {"ok": False, "error": "UNVERIFIED_INSTRUCTION", "message": "Prescription unclear; pharmacist/doctor must verify."}
    qty = 60
    payload = {"medication_id": m.id, "item": f"{m.name} {m.strength} tablets", "quantity": qty,
               "pharmacy": "Sanjeevani Pharmacy (sandbox)", "price_inr": 84, "delivery": "Tomorrow, 10 AM - 1 PM",
               "payment": "Cash on delivery (sandbox)"}
    activity(pid, sid, "Checked pharmacy stock & price", "done", f"{payload['item']} · in stock · ₹84", "get_pharmacy_quote")
    a = actions.create_approval(pid, sid, "refill_order", payload, {
        "title": "Order medicine refill", "lines": [f"{payload['item']} × {qty}", payload["pharmacy"],
                                                     f"₹{payload['price_inr']} · {payload['payment']}", payload["delivery"],
                                                     "Pharmacist will verify prescription"]})
    return {"ok": True, "approval_id": a.id, "quote": payload}


@tool
def prepare_doctor_brief(config: RunnableConfig) -> dict:
    """Create a pre-consultation brief for the doctor: conditions, medicines, latest values outside lab range,
    changes since previous report, and questions the patient may want to ask. Shows the brief card."""
    pid, sid = _ctx(config)
    with session() as s:
        p = s.get(Patient, pid)
    cmp = memory.compare(pid)["comparisons"]
    changes = [f"{c['test_name']}: {c['previous']} → {c['latest']} {c['unit']} (lab range {c['reference_range']})"
               for c in cmp if c["direction"] != "same"]
    meds = [f"{m['name']} {m['strength']} — {m['frequency'] or 'instruction unclear on source'}" for m in actions.medications_view(pid)]
    brief = {"patient": f"{p.name}, {p.age}{p.sex}", "conditions": p.conditions, "allergies": p.allergies,
             "medications": meds, "changes_since_last_report": changes,
             "questions": ["My HbA1c and LDL are higher than last time — what should change in my plan?",
                           "Atorvastatin instruction is unclear on my prescription — how should I take it?",
                           "When should I repeat these tests?"],
             "sources": ["Blood test report - 18 Nov 2026", "Blood test report - 09 May 2026",
                         "Consultation summary - Dr. Meera Rao", "Prescription - Dr. Meera Rao"]}
    activity(pid, sid, "Prepared doctor briefing", "done", f"{len(changes)} changes · {len(meds)} medicines", "prepare_brief")
    ui(pid, sid, "doctor_brief", brief)
    return {"ok": True, **brief}


@tool
def cancel_refill_order(config: RunnableConfig, order_ref: str = "") -> dict:
    """Cancel a sandbox pharmacy refill order (e.g. placed by mistake). Leave order_ref empty for the latest order."""
    pid, sid = _ctx(config)
    from .db import Approval
    with session() as s:
        q = select(Approval).where(Approval.patient_id == pid, Approval.action == "refill_order",
                                   Approval.status == "executed").order_by(Approval.created_at.desc())
        orders = list(s.scalars(q))
        a = next((o for o in orders if not order_ref or o.result.get("order_ref") == order_ref), None)
        if not a:
            return {"ok": False, "error": "NO_ORDER"}
        ref = a.result.get("order_ref")
        a.result = {**a.result, "status": "cancelled"}
        a.status = "cancelled"
    activity(pid, sid, "Pharmacy order cancelled", "done", f"{ref} (sandbox)", "cancel_order")
    return {"ok": True, "order_ref": ref, "status": "cancelled"}


ALL_TOOLS = [cancel_refill_order, get_patient_overview, get_lab_report, compare_lab_history, search_health_records, search_doctors,
             check_slots, propose_appointment, confirm_action, cancel_pending_action, propose_record_share,
             get_medications, propose_medication_reminders, propose_refill, prepare_doctor_brief]
