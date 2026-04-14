from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class UserMessage(BaseModel):
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AssistantDecision(BaseModel):
    decision_type: Literal["respond", "tool_call"] = "respond"
    response_text: str
    tool_name: str | None = None
    tool_args: dict[str, Any] = Field(default_factory=dict)


class OrchestratorResponse(BaseModel):
    response_text: str
    raw_decision: AssistantDecision
    approved: bool = True