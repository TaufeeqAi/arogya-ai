#!/usr/bin/env python3
"""Export JSON Schema files for Aarogya shared Pydantic contracts."""
from __future__ import annotations
import json
from pathlib import Path
import sys
from pydantic import TypeAdapter

ROOT = Path(__file__).resolve().parents[1]
PYTHON_CONTRACTS = ROOT / "contracts" / "python"
sys.path.insert(0, str(PYTHON_CONTRACTS))

from aarogya_contracts.agent import AgentEvent  # noqa: E402
from aarogya_contracts.ui import UIComponent  # noqa: E402
from aarogya_contracts.health import HealthObservation  # noqa: E402
from aarogya_contracts.medication import MedicationSchedulePreview  # noqa: E402
from aarogya_contracts.appointments import AppointmentBooking  # noqa: E402

OUT = ROOT / "contracts" / "events"
OUT.mkdir(parents=True, exist_ok=True)

schemas = {
    "agent-event.schema.json": AgentEvent.model_json_schema(),
    "ui-component.schema.json": TypeAdapter(UIComponent).json_schema(),
    "health-observation.schema.json": HealthObservation.model_json_schema(),
    "medication-schedule-preview.schema.json": MedicationSchedulePreview.model_json_schema(),
    "appointment-booking.schema.json": AppointmentBooking.model_json_schema(),
}

for filename, schema in schemas.items():
    path = OUT / filename
    path.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)}")
