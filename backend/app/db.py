"""Canonical structured store (PostgreSQL). Every row is patient-scoped where it holds patient data."""
from __future__ import annotations

import uuid
from contextlib import contextmanager
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def uid() -> str:
    return uuid.uuid4().hex[:12]


def now() -> datetime:
    return datetime.now(timezone.utc)


@contextmanager
def session():
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


class Base(DeclarativeBase):
    pass


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String)
    age: Mapped[int] = mapped_column(Integer)
    sex: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    area: Mapped[str] = mapped_column(String)
    language: Mapped[str] = mapped_column(String, default="hi-IN")
    conditions: Mapped[list] = mapped_column(JSON, default=list)
    allergies: Mapped[list] = mapped_column(JSON, default=list)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    title: Mapped[str] = mapped_column(String)
    doc_type: Mapped[str] = mapped_column(String)  # lab_report | prescription | consultation_note
    source_type: Mapped[str] = mapped_column(String)  # patient_upload | provider_import
    source_name: Mapped[str] = mapped_column(String)
    issued_on: Mapped[date] = mapped_column(Date)
    storage_key: Mapped[str] = mapped_column(String)
    mime_type: Mapped[str] = mapped_column(String, default="application/pdf")
    sha256: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="processed")  # uploaded|extracting|needs_review|processed|failed
    trust_label: Mapped[str] = mapped_column(String, default="provider_verified")
    text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Observation(Base):
    __tablename__ = "observations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    test_code: Mapped[str] = mapped_column(String, index=True)
    test_name: Mapped[str] = mapped_column(String)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String)
    ref_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    ref_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    ref_text: Mapped[str] = mapped_column(String)
    lab_flag: Mapped[str] = mapped_column(String, default="")  # H | L | "" exactly as printed by the lab
    observed_on: Mapped[date] = mapped_column(Date)
    page: Mapped[int] = mapped_column(Integer, default=1)
    validation_status: Mapped[str] = mapped_column(String, default="validated")


class Doctor(Base):
    __tablename__ = "doctors"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String)
    specialty: Mapped[str] = mapped_column(String)
    clinic: Mapped[str] = mapped_column(String)
    area: Mapped[str] = mapped_column(String)
    languages: Mapped[list] = mapped_column(JSON, default=list)
    fee: Mapped[int] = mapped_column(Integer)
    rating: Mapped[float] = mapped_column(Float)
    experience_years: Mapped[int] = mapped_column(Integer, default=10)


class Slot(Base):
    __tablename__ = "slots"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id"), index=True)
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    mode: Mapped[str] = mapped_column(String, default="in_person")
    status: Mapped[str] = mapped_column(String, default="open")  # open | booked


class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    session_id: Mapped[str] = mapped_column(String, default="")
    action: Mapped[str] = mapped_column(String)  # book_appointment | share_records | medication_reminders
    payload: Mapped[dict] = mapped_column(JSON)
    payload_hash: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|approved|rejected|expired|executed|failed
    decided_via: Mapped[str] = mapped_column(String, default="")
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (UniqueConstraint("idempotency_key"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id"))
    slot_id: Mapped[str] = mapped_column(ForeignKey("slots.id"), unique=True)
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String, default="confirmed")
    booking_ref: Mapped[str] = mapped_column(String)
    idempotency_key: Mapped[str] = mapped_column(String)
    calendar_url: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Medication(Base):
    __tablename__ = "medications"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    name: Mapped[str] = mapped_column(String)
    strength: Mapped[str] = mapped_column(String)
    frequency: Mapped[str | None] = mapped_column(String, nullable=True)
    times: Mapped[list] = mapped_column(JSON, default=list)  # ["08:00","20:00"]
    instructions: Mapped[str] = mapped_column(String, default="")
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_date: Mapped[date] = mapped_column(Date)
    supply_left_days: Mapped[int] = mapped_column(Integer, default=30)
    status: Mapped[str] = mapped_column(String, default="verified")  # verified | needs_clarification | reminders_active


class Reminder(Base):
    __tablename__ = "reminders"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    kind: Mapped[str] = mapped_column(String)  # medication | appointment | follow_up
    ref_id: Mapped[str] = mapped_column(String, default="")
    title: Mapped[str] = mapped_column(String)
    body: Mapped[str] = mapped_column(String, default="")
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    recurrence: Mapped[str] = mapped_column(String, default="")  # "" | daily
    status: Mapped[str] = mapped_column(String, default="scheduled")  # scheduled|sent|taken|skipped|snoozed|done
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class RecordShare(Base):
    __tablename__ = "record_shares"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id"))
    appointment_id: Mapped[str] = mapped_column(String, default="")
    document_ids: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="active")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AgentEvent(Base):
    __tablename__ = "agent_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(String, index=True)
    session_id: Mapped[str] = mapped_column(String, index=True, default="")
    type: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


def create_all() -> None:
    Base.metadata.create_all(engine)
