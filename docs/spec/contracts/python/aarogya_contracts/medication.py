from datetime import date, datetime, time
from typing import Literal
from pydantic import Field, field_validator, model_validator
from .common import StrictModel, SourceKind, VerificationStatus


class MedicationRecord(StrictModel):
    medication_id: str
    medication_name_original: str
    generic_name: str | None = None
    brand_name: str | None = None
    strength: str | None = None
    dosage_form: str | None = None
    route: str | None = None
    dosage_instruction: str | None = None
    frequency_instruction: str | None = None
    duration_instruction: str | None = None
    source_document_id: str | None = None
    source_kind: Literal["PROVIDER_AUTHORED", "PATIENT_UPLOAD", "PATIENT_REPORTED"]
    verification_status: Literal["REVIEW_REQUIRED", "PATIENT_CONFIRMED", "PROVIDER_VERIFIED", "REJECTED"]
    status: Literal["DRAFT", "ACTIVE", "COMPLETED", "DISCONTINUED", "SUPERSEDED", "REVIEW_REQUIRED"]


class MedicationSchedulePreview(StrictModel):
    medication_id: str
    timezone: str
    times_of_day: list[time] = Field(min_length=1)
    days_of_week: list[int] = Field(default_factory=lambda: list(range(7)), min_length=1)
    start_date: date
    end_date: date | None = None
    source_document_id: str
    source_verification_status: VerificationStatus
    patient_confirmation_required: bool = True

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, values: list[int]) -> list[int]:
        if any(value < 0 or value > 6 for value in values):
            raise ValueError("days_of_week uses 0=Monday through 6=Sunday")
        if len(set(values)) != len(values):
            raise ValueError("days_of_week must not contain duplicates")
        return values

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class AdherenceEvent(StrictModel):
    event_id: str
    medication_schedule_id: str
    reminder_occurrence_id: str | None = None
    reported_status: Literal["TAKEN_REPORTED", "SKIPPED_REPORTED", "SNOOZED"]
    reported_at: datetime
    source: Literal["PATIENT_APP", "VOICE_AGENT", "AUTHORIZED_CAREGIVER"]
    is_patient_reported: Literal[True] = True
