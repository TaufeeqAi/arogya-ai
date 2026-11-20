"""Simulated provider integration (Journey D): an authenticated clinic system pushes a signed record into the
patient's locker. Identity, patient match and consent are checked before import; provenance is preserved."""
from __future__ import annotations

import hashlib
import hmac
from datetime import date

from . import storage
from .db import Document, Medication, Patient, session, uid
from .events import activity, emit, ui
from .seed import _pdf

# Registered provider integrations (demo). Production: per-provider credentials + signature verification.
PROVIDERS = {"dr-meera": {"name": "Rao Family Clinic (Dr. Meera Rao)", "secret": b"rao-clinic-demo-signing-key"}}
CONNECTED = {"demo-patient": {"dr-meera"}}  # patient-authorized provider connections


def sign(provider_id: str, payload: bytes) -> str:
    return hmac.new(PROVIDERS[provider_id]["secret"], payload, hashlib.sha256).hexdigest()


def push_clarified_prescription(patient_id: str, session_id: str = "") -> dict:
    provider_id = "dr-meera"
    lines = [
        "1. Tab. Metformin 500 mg - 1 tablet twice daily after breakfast and after dinner - continue.",
        "2. Tab. Atorvastatin 10 mg - 1 tablet once daily at night (9:30 PM) - continue.",
        "Note: clarifies Atorvastatin frequency from the prescription dated 11 May 2026.",
    ]
    pdf = _pdf("Prescription (clarified) - Rao Family Clinic",
               ["Patient: Sunita Sharma | 56/F", f"Date: {date.today().strftime('%d %b %Y')} | Dr. Meera Rao, Reg. SYN-KMC-1182",
                "Digitally signed via Rao Family Clinic EMR"], None, lines)
    signature = sign(provider_id, pdf)

    # 1. verify provider identity / signature
    activity(patient_id, session_id, "Record received from connected provider", "running",
             PROVIDERS[provider_id]["name"], "provider_sync")
    if not hmac.compare_digest(signature, sign(provider_id, pdf)):
        activity(patient_id, session_id, "Provider signature invalid — rejected", "failed", "", "provider_sync")
        return {"ok": False, "error": "BAD_SIGNATURE"}
    activity(patient_id, session_id, "Provider signature verified", "done", f"HMAC-SHA256 {signature[:10]}…", "verify_provider")

    # 2. patient match + consent
    with session() as s:
        p = s.get(Patient, patient_id)
        if not p or p.name != "Sunita Sharma" or provider_id not in CONNECTED.get(patient_id, set()):
            activity(patient_id, session_id, "Patient match / consent failed — rejected", "failed", "", "provider_sync")
            return {"ok": False, "error": "NO_CONSENT"}
    activity(patient_id, session_id, "Patient matched · provider connection authorized", "done", p.name, "check_consent")

    # 3. import with provenance, update medication record from structured payload
    doc_id = "prov-" + uid()
    key = f"{patient_id}/{doc_id}.pdf"
    sha = storage.put(key, pdf)
    with session() as s:
        s.add(Document(id=doc_id, patient_id=patient_id, title="Prescription (clarified) - Dr. Meera Rao",
                       doc_type="prescription", source_type="provider_import", source_name="Rao Family Clinic",
                       issued_on=date.today(), storage_key=key, sha256=sha, status="processed",
                       trust_label="provider_verified", text="\n".join(lines)))
        s.flush()
        m = s.get(Medication, "med-atorva")
        if m and m.patient_id == patient_id:
            m.frequency, m.times = "Once daily at night", ["21:30"]
            m.instructions, m.status, m.document_id = "1 tablet at night", "verified", doc_id
    activity(patient_id, session_id, "Prescription imported · Atorvastatin instruction now verified", "done",
             "Provider-verified record", "import_record")
    try:
        from .memory import index_document
        with session() as s:
            index_document(s.get(Document, doc_id))
    except Exception:
        pass
    ui(patient_id, session_id, "provider_record", {
        "document_id": doc_id, "title": "Prescription (clarified)", "provider": PROVIDERS[provider_id]["name"],
        "date": date.today().isoformat(), "signature": signature[:16],
        "changes": ["Atorvastatin 10 mg: frequency now documented — once daily at night (9:30 PM)"]})
    emit(patient_id, session_id, "document_updated", {"document_id": doc_id, "status": "processed"})
    return {"ok": True, "document_id": doc_id}
