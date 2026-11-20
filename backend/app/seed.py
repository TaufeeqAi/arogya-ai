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
                 RecordShare, Reminder, Slot, engine, session)

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


def _lab_doc(s, when: date, lab: str, rows: list[tuple], doc_id: str) -> None:
    header = [f"Patient: Sunita Sharma | Age/Sex: 56/F | Patient ID: SYN-0042",
              f"Collected: {when.strftime('%d %b %Y')} | Laboratory: {lab}, Bengaluru",
              "Referred by: Dr. Meera Rao"]
    table = [["Test", "Result", "Unit", "Reference range", "Flag"]]
    text_lines = [f"Laboratory report from {lab} dated {when.isoformat()}."]
    for code, name, unit, lo, hi, ref, val in rows:
        f = _flag(val, lo, hi)
        table.append([name, str(val), unit, ref, f])
        text_lines.append(f"{name}: {val} {unit} (reference {ref}) {f}")
    notes = ["Flags (H/L) are printed by the laboratory against its reference range. Clinical correlation by the "
             "treating physician is advised."]
    pdf = _pdf(f"{lab} - Laboratory Report", header, table, notes)
    key = f"{PATIENT_ID}/{doc_id}.pdf"
    sha = storage.put(key, pdf)
    s.add(Document(id=doc_id, patient_id=PATIENT_ID, title=f"Blood test report - {when.strftime('%d %b %Y')}",
                   doc_type="lab_report", source_type="provider_import", source_name=lab, issued_on=when,
                   storage_key=key, sha256=sha, status="processed", trust_label="provider_verified",
                   text="\n".join(text_lines)))
    s.flush()
    for code, name, unit, lo, hi, ref, val in rows:
        s.add(Observation(patient_id=PATIENT_ID, document_id=doc_id, test_code=code, test_name=name, value=val,
                          unit=unit, ref_low=lo, ref_high=hi, ref_text=ref, lab_flag=_flag(val, lo, hi),
                          observed_on=when, page=1))


def reset_and_seed() -> None:
    Base.metadata.create_all(engine)
    with session() as s:
        for m in (AgentEvent, RecordShare, Reminder, Appointment, Approval, Slot, Doctor, Medication, Observation,
                  Document, Patient):
            s.execute(delete(m))

    with session() as s:
        s.add(Patient(id=PATIENT_ID, name="Sunita Sharma", age=56, sex="F", city="Bengaluru", area="Whitefield",
                      language="hi-IN", conditions=["Type 2 diabetes (since 2022)", "High cholesterol"],
                      allergies=["Penicillin"],
                      preferences={"preferred_time": "morning", "preferred_language": "Hindi/Hinglish",
                                   "preferred_doctor": "Dr. Meera Rao", "max_travel_km": 8}))
        s.flush()

        _lab_doc(s, MAY_REPORT, "Apex Diagnostics", [t[:7] for t in TESTS] + ONLY_MAY, "doc-lab-may")
        _lab_doc(s, NOV_REPORT, "Apex Diagnostics",
                 [(c, n, u, lo, hi, r, nov) for c, n, u, lo, hi, r, _may, nov in TESTS] + ONLY_NOV, "doc-lab-nov")

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

        # Prescription: one complete instruction, one deliberately incomplete (safety demo)
        rx = [
            "1. Tab. Metformin 500 mg - 1 tablet twice daily after breakfast and after dinner - 6 months.",
            "2. Tab. Atorvastatin 10 mg - ____ (frequency not legible on scanned copy).",
            "Advice: repeat HbA1c and lipid profile after 6 months.",
        ]
        pdf = _pdf("Prescription - Rao Family Clinic",
                   ["Patient: Sunita Sharma | 56/F", f"Date: {RX_DATE.strftime('%d %b %Y')} | Dr. Meera Rao, Reg. SYN-KMC-1182"],
                   None, rx)
        sha = storage.put(f"{PATIENT_ID}/doc-rx-may.pdf", pdf)
        s.add(Document(id="doc-rx-may", patient_id=PATIENT_ID, title="Prescription - Dr. Meera Rao",
                       doc_type="prescription", source_type="patient_upload", source_name="Rao Family Clinic",
                       issued_on=RX_DATE, storage_key=f"{PATIENT_ID}/doc-rx-may.pdf", sha256=sha,
                       trust_label="patient_uploaded", text="\n".join(rx)))
        s.flush()
        s.add(Medication(id="med-metformin", patient_id=PATIENT_ID, document_id="doc-rx-may", name="Metformin",
                         strength="500 mg", frequency="Twice daily", times=["08:30", "20:30"],
                         instructions="After breakfast and after dinner", duration_days=180, start_date=RX_DATE,
                         supply_left_days=4, status="verified"))
        s.add(Medication(id="med-atorva", patient_id=PATIENT_ID, document_id="doc-rx-may", name="Atorvastatin",
                         strength="10 mg", frequency=None, times=[], instructions="Frequency not legible on source",
                         duration_days=None, start_date=RX_DATE, supply_left_days=10, status="needs_clarification"))

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
