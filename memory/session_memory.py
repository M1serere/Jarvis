from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SessionMemory:
    history: list[dict[str, str]] = field(default_factory=list)

    def add_user_message(self, text: str) -> None:
        self.history.append({"role": "user", "text": text})

    def add_assistant_message(self, text: str) -> None:
        self.history.append({"role": "assistant", "text": text})

    def get_recent(self, limit: int = 10) -> list[dict[str, str]]:
        return self.history[-limit:]