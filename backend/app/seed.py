"""Deterministic synthetic demo data. No real patient information."""
from __future__ import annotations

import io
import zlib
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import delete

from . import storage
from .config import get_settings
from .db import (AgentEvent, Approval, Appointment, Base, Doctor, Document, Medication, Observation, Patient,
                 PharmacyOrder, RecordShare, Reminder, Slot, engine, session)

PATIENT_ID = "demo-patient"
TZ = ZoneInfo(get_settings().timezone)

# (code, name, unit, ref_low, ref_high, ref_text, value_may, value_nov)
TESTS = [
    ("HBA1C", "HbA1c (Glycated Haemoglobin)", "%", 4.0, 5.6, "4.0 - 5.6", 7.2, 8.1),
    ("FBS", "Fasting Blood Glucose", "mg/dL", 70, 99, "70 - 99", 138, 162),
    ("CHOL", "Total Cholesterol", "mg/dL", None, 200, "< 200", 192, 214),
    ("LDL", "LDL Cholesterol", "mg/dL", None, 100, "< 100", 118, 136),
    ("HDL", "HDL Cholesterol", "mg/dL", 50, None, "> 50", 46, 44),
    ("TG", "Triglycerides", "mg/dL", None, 150, "< 150", 160, 172),
    ("CREAT", "Serum Creatinine", "mg/dL", 0.5, 1.1, "0.5 - 1.1", 0.9, 0.9),
    ("HB", "Haemoglobin", "g/dL", 12.0, 15.5, "12.0 - 15.5", 12.4, 12.1),
]
ONLY_MAY = [("VITD", "Vitamin D (25-OH)", "ng/mL", 30, 100, "30 - 100", 18)]
ONLY_NOV = [("TSH", "TSH (Thyroid Stimulating Hormone)", "mIU/L", 0.4, 4.0, "0.4 - 4.0", 2.6)]

MAY_REPORT = date(2026, 5, 9)
NOV_REPORT = date(2026, 11, 18)
RX_DATE = date(2026, 5, 11)


def _flag(v, lo, hi):
    if lo is not None and v < lo:
        return "L"
    if hi is not None and v > hi:
        return "H"
    return ""


def _pdf(title: str, header_lines: list[str], table_rows: list[list[str]] | None, paragraphs: list[str]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=title)
    st = getSampleStyleSheet()
    flow = [Paragraph(f"<b>{title}</b>", st["Title"])]
    for h in header_lines:
        flow.append(Paragraph(h, st["Normal"]))
    flow.append(Spacer(1, 10))
    if table_rows:
        t = Table(table_rows, hAlign="LEFT", colWidths=[190, 70, 60, 90, 40])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        flow.append(t)
        flow.append(Spacer(1, 10))
    for p in paragraphs:
        flow.append(Paragraph(p, st["Normal"]))
        flow.append(Spacer(1, 6))
    flow.append(Spacer(1, 14))
    flow.append(Paragraph("<i>SYNTHETIC DEMONSTRATION DOCUMENT - not a real patient record.</i>", st["Normal"]))
    doc.build(flow)
    return buf.getvalue()


def _lab_doc(s, report_id: str, rep: dict, trust: str = "provider_verified", source_type: str = "provider_import") -> None:
    from . import labs
    when = date(*rep["date"])
    lab = rep["lab"]
    header = [f"Patient: Sunita Sharma | Age/Sex: 56/F | Patient ID: SYN-0042",
              f"Collected: {when.strftime('%d %b %Y')} | Laboratory: {lab}, Bengaluru",
              "Referred by: Dr. Meera Rao"]
    table = [["Test", "Result", "Unit", "Reference range", "Flag"]]
    text_lines = [f"Laboratory report from {lab} dated {when.isoformat()}."]
    current = None
    for code in labs.ORDER:
        if code not in rep["values"]:
            continue
        name, unit, lo, hi, ref, system, _ = labs.CATALOG[code]
        if system != current:
            current = system
            table.append([dict((k, t) for k, t, *_ in labs.SYSTEMS).get(system, system).upper(), "", "", "", ""])
        val = rep["values"][code]
        f = labs.flag(code, val)
        table.append([name, str(val), unit, ref, f])
        text_lines.append(f"{name}: {val} {unit} (reference {ref}) {f}")
    notes = ["Flags (H/L) are printed by the laboratory against its reference range. Clinical correlation by the "
             "treating physician is advised."]
    pdf = _pdf(f"{lab} - Laboratory Report", header, table, notes)
    key = f"{PATIENT_ID}/{report_id}.pdf"
    sha = storage.put(key, pdf)
    s.add(Document(id=report_id, patient_id=PATIENT_ID, title=f"Blood test report - {when.strftime('%d %b %Y')}",
                   doc_type="lab_report", source_type=source_type, source_name=lab, issued_on=when,
                   storage_key=key, sha256=sha, status="processed", trust_label=trust,
                   text="\n".join(text_lines)))
    s.flush()
    for code, val in rep["values"].items():
        name, unit, lo, hi, ref, *_ = labs.CATALOG[code]
        s.add(Observation(patient_id=PATIENT_ID, document_id=report_id, test_code=code, test_name=name, value=val,
                          unit=unit, ref_low=lo, ref_high=hi, ref_text=ref, lab_flag=labs.flag(code, val),
                          observed_on=when, page=1,
                          validation_status="validated" if trust == "provider_verified" else "patient_confirmed"))


def write_upload_demo_pdf(path: str) -> None:
    """The thyroid/vitamin panel used for the live upload demo (not seeded)."""
    from . import labs
    rep = labs.UPLOAD_DEMO
    when = date(*rep["date"])
    table = [["Test", "Result", "Unit", "Reference range", "Flag"]]
    for code in labs.ORDER:
        if code in rep["values"]:
            name, unit, lo, hi, ref, *_ = labs.CATALOG[code]
            table.append([name, str(rep["values"][code]), unit, ref, labs.flag(code, rep["values"][code])])
    pdf = _pdf(f"{rep['lab']} - Test Report",
               ["Patient: Sunita Sharma | Age/Sex: 56/F | Lab No: MPL-81904",
                f"Sample collected: {when.strftime('%d %b %Y')} | {rep['lab']}, Indiranagar, Bengaluru", "Ref. by: Self"],
               table, ["Results relate only to the sample tested. Flags indicate values outside the biological reference interval."])
    open(path, "wb").write(pdf)


def reset_and_seed() -> None:
    Base.metadata.create_all(engine)
    with session() as s:
        for m in (AgentEvent, PharmacyOrder, RecordShare, Reminder, Appointment, Approval, Slot, Doctor, Medication, Observation,
                  Document, Patient):
            s.execute(delete(m))

    with session() as s:
        s.add(Patient(id=PATIENT_ID, name="Sunita Sharma", age=56, sex="F", city="Bengaluru", area="Whitefield",
                      language="hi-IN", conditions=["Type 2 diabetes (since 2022)", "High cholesterol"],
                      allergies=["Penicillin"],
                      preferences={"preferred_time": "morning", "preferred_language": "Hindi/Hinglish",
                                   "preferred_doctor": "Dr. Meera Rao", "max_travel_km": 8}))
        s.flush()

        from . import labs
        for rid, rep in labs.REPORTS.items():
            if rid == "doc-lab-aug":  # a quick sugar check the patient uploaded and confirmed
                _lab_doc(s, rid, rep, trust="patient_confirmed", source_type="patient_upload")
            else:
                _lab_doc(s, rid, rep)

        # Consultation note (narrative -> semantic memory)
        note = [
            "Chief complaint: routine diabetes review. Patient reports occasional tiredness in the afternoons.",
            "Assessment documented by clinician: Type 2 diabetes, glycaemic control above target. LDL above target.",
            "Plan documented by clinician: continue Metformin 500 mg twice daily after meals. Start Atorvastatin "
            "(see prescription). Diet counselling given; walk 30 minutes daily.",
            "Follow-up: repeat HbA1c and lipid profile after 6 months and review with physician with reports.",
            "Patient reported allergy: Penicillin.",
        ]
        pdf = _pdf("Consultation Summary - Rao Family Clinic",
                   ["Patient: Sunita Sharma | 56/F", f"Date: {RX_DATE.strftime('%d %b %Y')} | Dr. Meera Rao, MBBS MD"],
                   None, note)
        sha = storage.put(f"{PATIENT_ID}/doc-note-may.pdf", pdf)
        s.add(Document(id="doc-note-may", patient_id=PATIENT_ID, title="Consultation summary - Dr. Meera Rao",
                       doc_type="consultation_note", source_type="provider_import", source_name="Rao Family Clinic",
                       issued_on=RX_DATE, storage_key=f"{PATIENT_ID}/doc-note-may.pdf", sha256=sha,
                       trust_label="provider_verified", text="\n".join(note)))

        # Prescription (May 2026, photo uploaded by patient): one clear instruction, one illegible, one stop order
        rx = [
            "1. Tab. Metformin 500 mg - 1 tablet twice daily after breakfast and after dinner - 6 months.",
            "2. Tab. Atorvastatin 10 mg - ____ (frequency not legible on scanned copy).",
            "3. STOP Tab. Glimepiride 1 mg (replaced by Metformin).",
            "Advice: repeat HbA1c and lipid profile after 6 months.",
        ]
        pdf = _pdf("Prescription - Rao Family Clinic",
                   ["Patient: Sunita Sharma | 56/F", f"Date: {RX_DATE.strftime('%d %b %Y')} | Dr. Meera Rao, Reg. SYN-KMC-1182"],
                   None, rx)
        sha = storage.put(f"{PATIENT_ID}/doc-rx-may.pdf", pdf)
        s.add(Document(id="doc-rx-may", patient_id=PATIENT_ID, title="Prescription - Dr. Meera Rao (May 2026)",
                       doc_type="prescription", source_type="patient_upload", source_name="Rao Family Clinic",
                       issued_on=RX_DATE, storage_key=f"{PATIENT_ID}/doc-rx-may.pdf", sha256=sha,
                       trust_label="patient_uploaded", text="\n".join(rx)))
        # Prescription (Nov 2025, synced from the clinic EMR): long-term medicines
        rx2_date = date(2025, 11, 14)
        rx2 = [
            "1. Tab. Telmisartan 40 mg - 1 tablet once daily in the morning (8:00 AM) - continue.",
            "2. Tab. Pantoprazole 40 mg - 1 tablet once daily before breakfast (7:30 AM) - continue.",
            "3. Tab. Calcium carbonate 500 mg - 1 tablet once daily after lunch (2:00 PM) - continue.",
            "4. Cap. Vitamin D3 60,000 IU - 1 capsule once a week on Sunday (9:00 AM) - continue.",
        ]
        pdf = _pdf("Prescription - Rao Family Clinic",
                   ["Patient: Sunita Sharma | 55/F", f"Date: {rx2_date.strftime('%d %b %Y')} | Dr. Meera Rao, Reg. SYN-KMC-1182",
                    "Digitally signed via Rao Family Clinic EMR"], None, rx2)
        sha = storage.put(f"{PATIENT_ID}/doc-rx-nov25.pdf", pdf)
        s.add(Document(id="doc-rx-nov25", patient_id=PATIENT_ID, title="Prescription - Dr. Meera Rao (Nov 2025)",
                       doc_type="prescription", source_type="provider_import", source_name="Rao Family Clinic",
                       issued_on=rx2_date, storage_key=f"{PATIENT_ID}/doc-rx-nov25.pdf", sha256=sha,
                       trust_label="provider_verified", text="\n".join(rx2)))
        s.flush()

        def med(mid, doc, name, strength, freq, times, instr, start, supply, status, days=None):
            s.add(Medication(id=mid, patient_id=PATIENT_ID, document_id=doc, name=name, strength=strength, frequency=freq,
                             times=times, instructions=instr, duration_days=days, start_date=start,
                             supply_left_days=supply, status=status))

        med("med-metformin", "doc-rx-may", "Metformin", "500 mg", "Twice daily", ["08:30", "20:30"],
            "After breakfast and after dinner", RX_DATE, 4, "verified", 180)
        med("med-atorva", "doc-rx-may", "Atorvastatin", "10 mg", None, [], "Frequency not legible on source",
            RX_DATE, 10, "needs_clarification")
        med("med-glimepiride", "doc-rx-may", "Glimepiride", "1 mg", None, [],
            "Stopped by Dr. Meera Rao on 11 May 2026 (replaced by Metformin). Do not restart without your doctor.",
            date(2024, 3, 1), 0, "stopped")
        med("med-telmisartan", "doc-rx-nov25", "Telmisartan", "40 mg", "Once daily", ["08:00"],
            "Morning, with or without food", rx2_date, 25, "reminders_active")
        med("med-pantoprazole", "doc-rx-nov25", "Pantoprazole", "40 mg", "Once daily", ["07:30"],
            "Before breakfast", rx2_date, 2, "verified")
        med("med-calcium", "doc-rx-nov25", "Calcium carbonate", "500 mg", "Once daily", ["14:00"],
            "After lunch", rx2_date, 15, "verified")
        med("med-vitd", "doc-rx-nov25", "Vitamin D3", "60,000 IU", "Once a week (Sunday)", ["SUN 09:00"],
            "After breakfast", rx2_date, 21, "reminders_active")

        # Already-active reminders + a week of self-reported adherence (Telmisartan)
        now_l = datetime.now(TZ)
        today8 = datetime.combine(now_l.date(), time(8, 0), TZ)
        for d_off, st in ((6, "taken"), (5, "taken"), (4, "skipped"), (3, "taken"), (2, "taken"), (1, "taken")):
            s.add(Reminder(patient_id=PATIENT_ID, kind="medication", ref_id="med-telmisartan", title="Telmisartan 40 mg",
                           body="Morning, with or without food", due_at=today8 - timedelta(days=d_off), status=st))
        if today8 <= now_l:
            s.add(Reminder(patient_id=PATIENT_ID, kind="medication", ref_id="med-telmisartan", title="Telmisartan 40 mg",
                           body="Morning, with or without food", due_at=today8, status="taken"))
            nxt = today8 + timedelta(days=1)
        else:
            nxt = today8
        s.add(Reminder(patient_id=PATIENT_ID, kind="medication", ref_id="med-telmisartan", title="Telmisartan 40 mg",
                       body="Morning, with or without food", due_at=nxt, recurrence="daily"))
        days_to_sun = (6 - now_l.weekday()) % 7
        sun9 = datetime.combine(now_l.date() + timedelta(days=days_to_sun), time(9, 0), TZ)
        if sun9 <= now_l:
            sun9 += timedelta(days=7)
        s.add(Reminder(patient_id=PATIENT_ID, kind="medication", ref_id="med-vitd", title="Vitamin D3 60,000 IU",
                       body="Weekly dose, after breakfast", due_at=sun9, recurrence="weekly"))

        # Clinician-documented follow-ups (from the 11 May consultation summary)
        s.add(Reminder(patient_id=PATIENT_ID, kind="follow_up", ref_id="doc-note-may", title="Repeat HbA1c and lipid profile",
                       body="Advised by Dr. Meera Rao on 11 May 2026: repeat after 6 months. Done: Apex Diagnostics report, 18 Nov 2026.",
                       due_at=datetime(2026, 11, 11, 9, 0, tzinfo=TZ), status="done"))
        s.add(Reminder(patient_id=PATIENT_ID, kind="follow_up", ref_id="doc-note-may", title="Review new reports with physician",
                       body="Advised by Dr. Meera Rao on 11 May 2026: review with physician with the repeat reports.",
                       due_at=datetime(2026, 11, 20, 10, 0, tzinfo=TZ), status="open"))

        # Doctors + slots (synthetic provider network)
        doctors = [
            Doctor(id="dr-meera", name="Dr. Meera Rao", specialty="General Physician", clinic="Rao Family Clinic",
                   area="Whitefield", languages=["Hindi", "English", "Kannada"], fee=600, rating=4.8, experience_years=18),
            Doctor(id="dr-arjun", name="Dr. Arjun Mehta", specialty="Endocrinologist (Diabetes)",
                   clinic="Sugar Care Centre", area="Indiranagar", languages=["Hindi", "English"], fee=900, rating=4.7,
                   experience_years=14),
            Doctor(id="dr-kavya", name="Dr. Kavya Iyer", specialty="Endocrinologist (Diabetes)",
                   clinic="Koramangala Endocrine Clinic", area="Koramangala", languages=["English", "Tamil", "Kannada"],
                   fee=1000, rating=4.9, experience_years=20),
            Doctor(id="dr-rahul", name="Dr. Rahul Verma", specialty="General Physician", clinic="Marathahalli Health Hub",
                   area="Marathahalli", languages=["Hindi", "English"], fee=500, rating=4.5, experience_years=9),
        ]
        s.add_all(doctors)
        s.flush()
        today = datetime.now(TZ).date()
        times = [time(9, 30), time(11, 0), time(12, 30), time(16, 0), time(17, 30)]
        for d in doctors:
            for day_off in range(0, 10):
                day = today + timedelta(days=day_off)
                if day.weekday() == 6:  # Sunday closed
                    continue
                for i, t in enumerate(times):
                    if (zlib.crc32(f'{d.id}{day_off}{i}'.encode()) % 5) == 0 and not (d.id == "dr-meera" and day.weekday() == 5):
                        continue  # some slots already taken
                    s.add(Slot(doctor_id=d.id, start=datetime.combine(day, t, TZ), mode="in_person"))
    index_documents()


def index_documents() -> None:
    try:
        from .memory import index_all_documents
        index_all_documents(PATIENT_ID)
    except Exception as e:  # semantic memory is an enhancement; structured memory still works
        print("WARN: semantic indexing skipped:", e)


if __name__ == "__main__":
    reset_and_seed()
    print("seeded")
