from __future__ import annotations

import re

from brain.adapters.base import BaseBrainAdapter
from core.models import AssistantDecision


class MockBrainAdapter(BaseBrainAdapter):
    URL_PATTERN = re.compile(
        r"(https?://[^\s]+|[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)"
    )

    CREATE_FILE_PATTERN = re.compile(
        r"создай файл\s+([^\s]+)",
        re.IGNORECASE,
    )

    OPEN_FILE_PATTERN = re.compile(
        r"открой файл\s+([^\s]+)",
        re.IGNORECASE,
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
                response_text="Работаю стабильно. Теперь я уже умею открывать сайты, искать в Google и работать с файлами."
            )

        if "что ты умеешь" in text:
            return AssistantDecision(
                decision_type="respond",
                response_text=(
                    "Сейчас я умею отвечать текстом, открывать сайты, выполнять поиск в Google, "
                    "создавать файлы и читать файлы из рабочей папки."
                )
            )

        create_filename = self._extract_create_file_name(user_text)
        if create_filename:
            return AssistantDecision(
                decision_type="tool_call",
                tool_name="create_file",
                tool_args={"filename": create_filename, "content": ""},
            )

        open_filename = self._extract_open_file_name(user_text)
        if open_filename:
            return AssistantDecision(
                decision_type="tool_call",
                tool_name="open_file",
                tool_args={"filename": open_filename},
            )

        search_query = self._extract_search_query(user_text)
        if search_query:
            return AssistantDecision(
                decision_type="tool_call",
                tool_name="browser_search",
                tool_args={"query": search_query},
            )

        if any(phrase in text for phrase in ["открой сайт", "открой", "open"]):
            url = self._extract_url(user_text)
            if url:
                return AssistantDecision(
                    decision_type="tool_call",
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
                f"Сейчас я работаю через MockBrainAdapter и умею вызывать несколько инструментов."
            )
        )

    def _extract_url(self, text: str) -> str | None:
        match = self.URL_PATTERN.search(text)
        if match:
            return match.group(1)
        return None

    def _extract_search_query(self, text: str) -> str | None:
        lowered = text.lower().strip()

        prefixes = [
            "найди в гугле ",
            "поищи в гугле ",
            "найди в google ",
            "поищи в google ",
            "search google ",
            "google ",
        ]

        for prefix in prefixes:
            if lowered.startswith(prefix):
                return text[len(prefix):].strip()

        return None

    def _extract_create_file_name(self, text: str) -> str | None:
        match = self.CREATE_FILE_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        return None

    def _extract_open_file_name(self, text: str) -> str | None:
        match = self.OPEN_FILE_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        return None