"""Agent event bus: persisted to Postgres (audit) and fanned out over Redis pub/sub to SSE clients."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import redis

from .config import get_settings
from .db import AgentEvent, session

_r = redis.Redis.from_url(get_settings().redis_url, decode_responses=True)


def channel(patient_id: str) -> str:
    return f"aarogya:events:{patient_id}"


def emit(patient_id: str, session_id: str, type_: str, payload: dict) -> dict:
    evt = {
        "type": type_,
        "session_id": session_id,
        "payload": payload,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    try:
        with session() as s:
            s.add(AgentEvent(patient_id=patient_id, session_id=session_id, type=type_, payload=payload))
    except Exception:  # audit failure must not break the conversation
        pass
    _r.publish(channel(patient_id), json.dumps(evt, default=str))
    return evt


def activity(patient_id: str, session_id: str, label: str, status: str = "done", detail: str = "", tool: str = "") -> None:
    emit(patient_id, session_id, "activity", {"label": label, "status": status, "detail": detail, "tool": tool})


def ui(patient_id: str, session_id: str, component: str, props: dict) -> None:
    emit(patient_id, session_id, "ui", {"component": component, "version": 1, "props": props})
