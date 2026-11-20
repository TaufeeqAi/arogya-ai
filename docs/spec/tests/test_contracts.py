from datetime import date, datetime, time, timezone
from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from aarogya_contracts.agent import AgentEvent
from aarogya_contracts.health import HealthObservation, ReferenceRange
from aarogya_contracts.medication import MedicationSchedulePreview
from aarogya_contracts.ui import UIComponent


def test_health_observation_requires_value_and_source():
    observation = HealthObservation(
        observation_id="obs-1",
        patient_ref="patient-1",
        document_id="doc-1",
        test_name_original="Synthetic analyte",
        value_numeric=Decimal("1.25"),
        unit_original="mg/dL",
        observed_at=datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc),
        evidence={
            "document_id": "doc-1",
            "source_kind": "PATIENT_UPLOAD",
            "verification_status": "PATIENT_ATTESTED",
        },
        verification_status="PATIENT_CONFIRMED",
    )
    assert observation.value_numeric == Decimal("1.25")

    with pytest.raises(ValidationError):
        HealthObservation(
            observation_id="obs-2",
            patient_ref="patient-1",
            document_id="doc-1",
            test_name_original="Synthetic analyte",
            evidence={
                "document_id": "doc-1",
                "source_kind": "PATIENT_UPLOAD",
                "verification_status": "PATIENT_ATTESTED",
            },
            verification_status="REVIEW_REQUIRED",
        )


def test_reference_range_rejects_inverted_bounds():
    with pytest.raises(ValidationError):
        ReferenceRange(low=Decimal("2"), high=Decimal("1"))


def test_medication_schedule_requires_valid_days_and_dates():
    schedule = MedicationSchedulePreview(
        medication_id="med-1",
        timezone="Asia/Kolkata",
        times_of_day=[time(8, 0)],
        days_of_week=[0, 1, 2, 3, 4, 5, 6],
        start_date=date(2026, 11, 21),
        source_document_id="doc-1",
        source_verification_status="PROVIDER_VERIFIED",
    )
    assert schedule.timezone == "Asia/Kolkata"

    with pytest.raises(ValidationError):
        MedicationSchedulePreview(
            medication_id="med-1",
            timezone="Asia/Kolkata",
            times_of_day=[time(8, 0)],
            days_of_week=[7],
            start_date=date(2026, 11, 21),
            source_document_id="doc-1",
            source_verification_status="PROVIDER_VERIFIED",
        )


def test_ui_component_is_discriminated_and_rejects_unknown_component():
    adapter = TypeAdapter(UIComponent)
    component = adapter.validate_python({
        "component": "health_summary",
        "version": "1",
        "payload": {"heading": "Summary", "summary": "Synthetic only", "evidence": []},
    })
    assert component.component == "health_summary"

    with pytest.raises(ValidationError):
        adapter.validate_python({"component": "arbitrary_html", "payload": {}})


def test_agent_event_requires_timezone_aware_timestamp():
    event = AgentEvent(
        event_id="evt-1",
        conversation_id="conv-1",
        sequence=1,
        occurred_at=datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc),
        type="agent.session.started",
        payload={},
    )
    assert event.schema_version == "1.0"

    with pytest.raises(ValidationError):
        AgentEvent(
            event_id="evt-2",
            conversation_id="conv-1",
            sequence=2,
            occurred_at=datetime(2026, 11, 21, 10, 0),
            type="agent.session.started",
            payload={},
        )
