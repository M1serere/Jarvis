from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
from typing import Any, Literal


@dataclass(slots=True)
class UserMessage:
    text: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class AssistantDecision:
    decision_type: Literal["respond", "tool_call"] = "respond"
    response_text: str = ""
    tool_name: str | None = None
    tool_args: dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False

    def model_dump_json(self) -> str:
        return json.dumps(asdict(self), default=str, ensure_ascii=False)


@dataclass(slots=True)
class OrchestratorResponse:
    response_text: str
    raw_decision: AssistantDecision
    approved: bool = True


def empty_decision() -> AssistantDecision:
    return AssistantDecision(
        decision_type="respond",
        response_text="",
        tool_name=None,
        tool_args={},
        requires_confirmation=False,
    )
