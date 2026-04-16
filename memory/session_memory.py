from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PendingAction:
    tool_name: str
    tool_args: dict[str, Any]
    confirmation_message: str


@dataclass
class SessionMemory:
    history: list[dict[str, str]] = field(default_factory=list)
    pending_action: PendingAction | None = None
    last_file: str | None = None

    def add_user_message(self, text: str) -> None:
        self.history.append({"role": "user", "text": text})

    def add_assistant_message(self, text: str) -> None:
        self.history.append({"role": "assistant", "text": text})

    def get_recent(self, limit: int = 10) -> list[dict[str, str]]:
        return self.history[-limit:]

    def set_pending_action(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        confirmation_message: str,
    ) -> None:
        self.pending_action = PendingAction(
            tool_name=tool_name,
            tool_args=tool_args,
            confirmation_message=confirmation_message,
        )

    def get_pending_action(self) -> PendingAction | None:
        return self.pending_action

    def clear_pending_action(self) -> None:
        self.pending_action = None

    def set_last_file(self, filename: str) -> None:
        self.last_file = filename

    def get_last_file(self) -> str | None:
        return self.last_file