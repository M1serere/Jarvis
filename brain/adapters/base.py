from __future__ import annotations

from abc import ABC, abstractmethod

from core.models import AssistantDecision


class BaseBrainAdapter(ABC):
    @abstractmethod
    def decide(
        self,
        user_text: str,
        conversation_context: list[dict[str, str]],
        system_prompt: str,
        available_tools: list[dict[str, str]] | None = None,
    ) -> AssistantDecision:
        """Return the assistant decision for the current turn."""
        raise NotImplementedError