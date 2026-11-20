from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import Field, model_validator
from .common import StrictModel, EvidenceReference, SourceKind, VerificationStatus


class ReferenceRange(StrictModel):
    low: Decimal | None = None
    high: Decimal | None = None
    original_text: str | None = None
    unit: str | None = None

    @model_validator(mode="after")
    def validate_order(self):
        if self.low is not None and self.high is not None and self.low > self.high:
            raise ValueError("reference range low must not exceed high")
        return self


class HealthObservation(StrictModel):
    observation_id: str
    patient_ref: str
    document_id: str
    test_name_original: str
    test_name_normalized: str | None = None
    test_code_system: str | None = None
    test_code: str | None = None
    value_numeric: Decimal | None = None
    value_text: str | None = None
    unit_original: str | None = None
    unit_normalized: str | None = None
    reference_range: ReferenceRange | None = None
    laboratory_interpretation: str | None = None
    observed_at: datetime | None = None
    laboratory_name: str | None = None
    evidence: EvidenceReference
    extraction_confidence: Decimal | None = Field(default=None, ge=0, le=1)
    verification_status: VerificationStatus

    @model_validator(mode="after")
    def require_value(self):
        if self.value_numeric is None and not self.value_text:
            raise ValueError("one of value_numeric or value_text is required")
        return self


class HealthDocument(StrictModel):
    document_id: str
    document_type: Literal[
        "LAB_REPORT", "PRESCRIPTION", "CONSULTATION_NOTE", "DISCHARGE_SUMMARY",
        "RADIOLOGY_REPORT", "MEDICAL_CERTIFICATE", "INSURANCE_POLICY", "OTHER", "UNKNOWN"
    ]
    source_kind: SourceKind
    source_verification_status: VerificationStatus
    original_filename: str
    mime_type: str
    received_at: datetime
    document_status: Literal[
        "UPLOADED", "QUEUED", "PROCESSING", "NEEDS_REVIEW", "READY", "FAILED", "QUARANTINED", "ARCHIVED"
    ]
    page_count: int | None = Field(default=None, ge=1)


class ObservationComparisonPoint(StrictModel):
    observation_id: str
    observed_at: datetime
    value: Decimal
    unit: str
    reference_range: ReferenceRange | None = None
    evidence: EvidenceReference


class ObservationComparisonResponse(StrictModel):
    test_name: str
    comparable: bool
    comparability_reason: str
    normalized_unit: str | None = None
    calculation_method_version: str | None = None
    points: list[ObservationComparisonPoint] = Field(default_factory=list)
    absolute_difference: Decimal | None = None
    percentage_difference: Decimal | None = None
    clinical_interpretation: Literal["NOT_PROVIDED"] = "NOT_PROVIDED"
