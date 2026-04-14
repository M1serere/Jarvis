from __future__ import annotations

from brain.adapters.base import BaseBrainAdapter
from brain.adapters.mock_adapter import MockBrainAdapter
from brain.prompts import JARVIS_SYSTEM_PROMPT
from core.models import AssistantDecision


class Brain:
    def __init__(self, adapter: BaseBrainAdapter | None = None) -> None:
        self.adapter = adapter or MockBrainAdapter()
        self.system_prompt = JARVIS_SYSTEM_PROMPT

    def decide(
        self,
        user_text: str,
        conversation_context: list[dict[str, str]],
    ) -> AssistantDecision:
        return self.adapter.decide(
            user_text=user_text,
            conversation_context=conversation_context,
            system_prompt=self.system_prompt,
        )