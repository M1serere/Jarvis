from __future__ import annotations

from core.models import AssistantDecision, UserMessage


class Brain:
    def decide(self, message: UserMessage) -> AssistantDecision:
        text = message.text.lower()

        if "привет" in text:
            return AssistantDecision(
                decision_type="respond",
                response_text="Привет. Я на связи."
            )

        if "как дела" in text:
            return AssistantDecision(
                decision_type="respond",
                response_text="Работаю в тестовом режиме. Но ядро уже запускается."
            )

        return AssistantDecision(
            decision_type="respond",
            response_text=f"Я получил сообщение: '{message.text}'. Пока я работаю без настоящей модели, но core уже готов."
        )