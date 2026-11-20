from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


SourceKind = Literal[
    "PATIENT_UPLOAD", "PROVIDER_IMPORT", "LAB_IMPORT", "PATIENT_REPORTED", "PROVIDER_AUTHORED", "SYSTEM_DERIVED"
]
VerificationStatus = Literal[
    "UNVERIFIED", "PATIENT_ATTESTED", "PATIENT_CONFIRMED", "PROVIDER_AUTHENTICATED",
    "PROVIDER_VERIFIED", "REVIEW_REQUIRED", "REJECTED", "SOURCE_ONLY"
]


class EvidenceReference(StrictModel):
    document_id: str
    page_number: int | None = Field(default=None, ge=1)
    source_locator: str | None = None
    source_kind: SourceKind
    verification_status: VerificationStatus
    observed_at: datetime | None = None


class APIError(StrictModel):
    code: str
    message: str
    retryable: bool = False
    request_id: str
    details: dict = Field(default_factory=dict)


class Timestamped(StrictModel):
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value
