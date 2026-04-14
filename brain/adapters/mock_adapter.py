from __future__ import annotations

import re

from brain.adapters.base import BaseBrainAdapter
from core.models import AssistantDecision


class MockBrainAdapter(BaseBrainAdapter):
    URL_PATTERN = re.compile(
        r"(https?://[^\s]+|[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)"
    )

    def decide(
        self,
        user_text: str,
        conversation_context: list[dict[str, str]],
        system_prompt: str,
    ) -> AssistantDecision:
        text = user_text.lower().strip()

        if "привет" in text:
            return AssistantDecision(
                decision_type="respond",
                response_text="Привет. Я на связи."
            )

        if "как дела" in text:
            return AssistantDecision(
                decision_type="respond",
                response_text="Работаю стабильно. Теперь я уже умею вызывать инструменты."
            )

        if "что ты умеешь" in text:
            return AssistantDecision(
                decision_type="respond",
                response_text=(
                    "Сейчас я умею отвечать текстом и вызывать первый инструмент: "
                    "открытие сайтов в браузере."
                )
            )

        if any(phrase in text for phrase in ["открой сайт", "открой", "open"]):
            url = self._extract_url(user_text)
            if url:
                return AssistantDecision(
                    decision_type="tool_call",
                    response_text="",
                    tool_name="open_url",
                    tool_args={"url": url},
                )

            return AssistantDecision(
                decision_type="respond",
                response_text="Я понял, что нужно открыть сайт, но не увидел адрес."
            )

        return AssistantDecision(
            decision_type="respond",
            response_text=(
                f"Я получил сообщение: '{user_text}'. "
                f"Сейчас я работаю через MockBrainAdapter и умею вызывать инструмент open_url."
            )
        )

    def _extract_url(self, text: str) -> str | None:
        match = self.URL_PATTERN.search(text)
        if match:
            return match.group(1)
        return None