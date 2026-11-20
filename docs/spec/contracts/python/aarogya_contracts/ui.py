from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Union
from pydantic import Field
from .common import StrictModel, EvidenceReference
from .health import ReferenceRange
from .appointments import AppointmentSlot, ProviderSummary
from .medication import MedicationSchedulePreview


class HealthSummaryPayload(StrictModel):
    heading: str
    summary: str
    evidence: list[EvidenceReference] = Field(default_factory=list)
    qualification: str | None = None


class HealthSummaryComponent(StrictModel):
    component: Literal["health_summary"]
    version: Literal["1"] = "1"
    payload: HealthSummaryPayload


class LabObservationPayload(StrictModel):
    observation_id: str
    test_name: str
    value_numeric: Decimal | None = None
    value_text: str | None = None
    unit: str | None = None
    reference_range: ReferenceRange | None = None
    laboratory_interpretation: str | None = None
    observed_at: datetime | None = None
    evidence: EvidenceReference


class LabObservationComponent(StrictModel):
    component: Literal["lab_observation"]
    version: Literal["1"] = "1"
    payload: LabObservationPayload


class AppointmentSlotsPayload(StrictModel):
    provider: ProviderSummary
    slots: list[AppointmentSlot]
    availability_note: str | None = None


class AppointmentSlotsComponent(StrictModel):
    component: Literal["appointment_slots"]
    version: Literal["1"] = "1"
    payload: AppointmentSlotsPayload


class MedicationSchedulePayload(StrictModel):
    medication_name: str
    schedule: MedicationSchedulePreview
    status: Literal["PREVIEW", "PENDING_CONFIRMATION", "ACTIVE"]


class MedicationScheduleComponent(StrictModel):
    component: Literal["medication_schedule"]
    version: Literal["1"] = "1"
    payload: MedicationSchedulePayload


class ApprovalCardPayload(StrictModel):
    approval_id: str
    action_type: str
    summary: str
    payload_hash: str
    expires_at: datetime
    exact_details: dict


class ApprovalCardComponent(StrictModel):
    component: Literal["approval_card"]
    version: Literal["1"] = "1"
    payload: ApprovalCardPayload


UIComponent = Annotated[
    Union[
        HealthSummaryComponent,
        LabObservationComponent,
        AppointmentSlotsComponent,
        MedicationScheduleComponent,
        ApprovalCardComponent,
    ],
    Field(discriminator="component"),
]
