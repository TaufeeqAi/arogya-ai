from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import Field, model_validator
from .common import StrictModel


class ProviderSummary(StrictModel):
    provider_id: str
    display_name: str
    specialty: str
    verification_status: Literal["UNVERIFIED", "PENDING", "VERIFIED", "REJECTED"]
    clinic_id: str
    clinic_name: str
    locality: str | None = None
    city: str | None = None
    source_kind: Literal["DEMO", "PARTNER_API", "PROVIDER_PORTAL"]


class AppointmentSlot(StrictModel):
    slot_id: str
    provider_id: str
    clinic_id: str
    starts_at: datetime
    ends_at: datetime
    timezone: str
    consultation_mode: Literal["IN_PERSON", "VIDEO", "PHONE"]
    availability_status: Literal["AVAILABLE", "HELD", "BOOKED", "UNAVAILABLE", "EXPIRED"]
    fetched_at: datetime
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def validate_times(self):
        for value in (self.starts_at, self.ends_at, self.fetched_at):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("timestamps must be timezone-aware")
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at")
        return self


class AppointmentBooking(StrictModel):
    appointment_id: str
    provider: ProviderSummary
    slot: AppointmentSlot
    status: Literal[
        "REQUESTED", "PENDING_APPROVAL", "BOOKING", "CONFIRMED", "CANCEL_PENDING",
        "CANCELLED", "FAILED", "UNKNOWN", "COMPLETED", "NO_SHOW"
    ]
    external_booking_reference: str | None = None
    confirmed_at: datetime | None = None
    fee_amount: Decimal | None = Field(default=None, ge=0)
    currency: str | None = None
