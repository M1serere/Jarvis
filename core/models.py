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

    @classmethod
    def model_json_schema(cls) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "decision_type": {
                    "type": "string",
                    "enum": ["respond", "tool_call"],
                },
                "response_text": {"type": "string"},
                "tool_name": {"type": ["string", "null"]},
                "tool_args": {"type": "object"},
                "requires_confirmation": {"type": "boolean"},
            },
            "required": [
                "decision_type",
                "response_text",
                "tool_name",
                "tool_args",
                "requires_confirmation",
            ],
            "additionalProperties": False,
        }

    @classmethod
    def model_validate(cls, data: Any) -> "AssistantDecision":
        if not isinstance(data, dict):
            raise TypeError("AssistantDecision payload must be a dict")

        decision_type = data.get("decision_type", "respond")
        if decision_type not in {"respond", "tool_call"}:
            raise ValueError("Invalid decision_type")

        response_text = data.get("response_text", "")
        if not isinstance(response_text, str):
            raise TypeError("response_text must be a string")

        tool_name = data.get("tool_name")
        if tool_name is not None and not isinstance(tool_name, str):
            raise TypeError("tool_name must be a string or null")

        tool_args = data.get("tool_args", {})
        if not isinstance(tool_args, dict):
            raise TypeError("tool_args must be an object")

        requires_confirmation = data.get("requires_confirmation", False)
        if not isinstance(requires_confirmation, bool):
            raise TypeError("requires_confirmation must be a boolean")

        return cls(
            decision_type=decision_type,
            response_text=response_text,
            tool_name=tool_name,
            tool_args=tool_args,
            requires_confirmation=requires_confirmation,
        )

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    def model_dump_json(self) -> str:
        return json.dumps(self.model_dump(), default=str, ensure_ascii=False)


@dataclass(slots=True)
class OrchestratorResponse:
    response_text: str
    raw_decision: AssistantDecision
    approved: bool = True
    keep_awake: bool = True


def empty_decision() -> AssistantDecision:
    return AssistantDecision(
        decision_type="respond",
        response_text="",
        tool_name=None,
        tool_args={},
        requires_confirmation=False,
    )
