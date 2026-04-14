from __future__ import annotations

from core.models import AssistantDecision
from brain.adapters.base import BaseBrainAdapter


class MockBrainAdapter(BaseBrainAdapter):
    def decide(
        self,
        user_text: str,
        conversation_context: list[dict[str, str]],
        system_prompt: str,
    ) -> AssistantDecision:
        text = user_text.lower()

        if "привет" in text:
            return AssistantDecision(
                decision_type="respond",
                response_text="Привет. Я на связи."
            )

        if "как дела" in text:
            return AssistantDecision(
                decision_type="respond",
                response_text="Работаю стабильно. Архитектура мозга уже отделена от оркестратора."
            )

        if "что ты умеешь" in text:
            return AssistantDecision(
                decision_type="respond",
                response_text=(
                    "Пока я работаю в тестовом режиме. "
                    "Сейчас у меня есть оркестратор, память сессии, логирование "
                    "и отдельный слой brain adapter для будущей модели."
                )
            )

        return AssistantDecision(
            decision_type="respond",
            response_text=(
                f"Я получил сообщение: '{user_text}'. "
                f"Сейчас я отвечаю через MockBrainAdapter. "
                f"В следующем этапе сюда можно будет подключить реальную модель."
            )
        )