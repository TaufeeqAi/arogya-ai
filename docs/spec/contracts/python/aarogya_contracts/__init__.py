"""Aarogya public API and event contract models.

These Pydantic models are the canonical starter contracts. Extend them in a
backwards-compatible way and export OpenAPI from the FastAPI application.
"""

from .common import APIError, EvidenceReference
from .health import HealthDocument, HealthObservation, ObservationComparisonResponse
from .medication import MedicationRecord, MedicationSchedulePreview, AdherenceEvent
from .appointments import ProviderSummary, AppointmentSlot, AppointmentBooking
from .agent import AgentEvent, AgentSessionCreateRequest, AgentActionDecisionRequest
from .ui import UIComponent

__all__ = [
    "APIError", "EvidenceReference", "HealthDocument", "HealthObservation",
    "ObservationComparisonResponse", "MedicationRecord", "MedicationSchedulePreview",
    "AdherenceEvent", "ProviderSummary", "AppointmentSlot", "AppointmentBooking",
    "AgentEvent", "AgentSessionCreateRequest", "AgentActionDecisionRequest", "UIComponent",
]
