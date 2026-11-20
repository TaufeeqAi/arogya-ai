from datetime import datetime
from typing import Literal
from pydantic import Field, model_validator
from .common import StrictModel


class AgentSessionCreateRequest(StrictModel):
    preferred_language: str
    client_platform: Literal["IOS", "ANDROID", "WEB"]


class AgentSessionResponse(StrictModel):
    conversation_id: str
    provider_session_id: str
    client_token: str
    token_expires_at: datetime
    voice_provider: str
    language: str


class AgentActionDecisionRequest(StrictModel):
    decision: Literal["APPROVE", "REJECT"]
    expected_payload_hash: str
    decision_note: str | None = None


class AgentEvent(StrictModel):
    schema_version: str = "1.0"
    event_id: str
    conversation_id: str
    workflow_run_id: str | None = None
    sequence: int = Field(ge=0)
    occurred_at: datetime
    type: Literal[
        "agent.session.started", "agent.status.changed",
        "conversation.transcript.partial", "conversation.transcript.final",
        "assistant.message.started", "assistant.message.delta", "assistant.message.completed",
        "ui.component.render", "ui.component.update",
        "tool.execution.started", "tool.execution.completed", "tool.execution.failed",
        "approval.required", "approval.completed", "approval.rejected", "approval.expired",
        "workflow.completed", "workflow.failed", "safety.notice"
    ]
    payload: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_timezone(self):
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
        return self
