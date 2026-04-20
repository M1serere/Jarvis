from __future__ import annotations

import requests

from brain.adapters.base import BaseBrainAdapter
from brain.adapters.mock_adapter import MockBrainAdapter
from brain.adapters.ollama_adapter import OllamaBrainAdapter
from brain.prompts import JARVIS_SYSTEM_PROMPT
from core.config import BRAIN_PROVIDER
from core.logger import setup_logger
from core.models import AssistantDecision


class Brain:
    def __init__(self, adapter: BaseBrainAdapter | None = None) -> None:
        self.logger = setup_logger()
        self.adapter = adapter or self._build_default_adapter()
        self.fallback_adapter = MockBrainAdapter()
        self.system_prompt = JARVIS_SYSTEM_PROMPT

    def _build_default_adapter(self) -> BaseBrainAdapter:
        if BRAIN_PROVIDER == "ollama":
            return OllamaBrainAdapter()
        return MockBrainAdapter()

    def decide(
        self,
        user_text: str,
        conversation_context: list[dict[str, str]],
        available_tools: list[dict[str, str]] | None = None,
    ) -> AssistantDecision:
        try:
            return self.adapter.decide(
                user_text=user_text,
                conversation_context=conversation_context,
                system_prompt=self.system_prompt,
                available_tools=available_tools or [],
            )
        except requests.RequestException as exc:
            if isinstance(self.adapter, OllamaBrainAdapter):
                self.logger.warning(
                    "Ollama is unavailable, switching to fallback adapter: %s",
                    exc,
                )
                return self.fallback_adapter.decide(
                    user_text=user_text,
                    conversation_context=conversation_context,
                    system_prompt=self.system_prompt,
                    available_tools=available_tools or [],
                )
            raise
