from __future__ import annotations

import re

from brain.adapters.base import BaseBrainAdapter
from core.models import AssistantDecision


class MockBrainAdapter(BaseBrainAdapter):
    URL_PATTERN = re.compile(
        r"(https?://[^\s]+|[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)"
    )

    CREATE_FILE_WITH_TEXT_PATTERN = re.compile(
        r"создай файл\s+([^\s]+)\s+с текстом\s+(.+)",
        re.IGNORECASE,
    )
    CREATE_FILE_PATTERN = re.compile(
        r"создай файл\s+([^\s]+)",
        re.IGNORECASE,
    )
    OPEN_FILE_PATTERN = re.compile(
        r"открой файл\s+([^\s]+)",
        re.IGNORECASE,
    )
    APPEND_FILE_PATTERN = re.compile(
        r"добавь в файл\s+([^\s]+)\s+текст\s+(.+)",
        re.IGNORECASE,
    )
    REPLACE_FILE_TEXT_PATTERN = re.compile(
        r"замени в файле\s+([^\s]+)\s+(.+)\s+на\s+(.+)",
        re.IGNORECASE,
    )
    REWRITE_FILE_PATTERN = re.compile(
        r"измени файл\s+([^\s]+)\s+на текст\s+(.+)",
        re.IGNORECASE,
    )
    DELETE_FILE_PATTERN = re.compile(
        r"удали файл\s+([^\s]+)",
        re.IGNORECASE,
    )

    def decide(
        self,
        user_text: str,
        conversation_context: list[dict[str, str]],
        system_prompt: str,
        available_tools: list[dict[str, str]] | None = None,
    ) -> AssistantDecision:
        text = user_text.lower().strip()

        if "привет" in text:
            return AssistantDecision(
                decision_type="respond",
                response_text="Привет. Я на связи.",
            )

        if "как дела" in text:
            return AssistantDecision(
                decision_type="respond",
                response_text="Работаю стабильно. Сейчас я в fallback-режиме без Ollama.",
            )

        if "что ты умеешь" in text:
            return AssistantDecision(
                decision_type="respond",
                response_text=(
                    "Я могу отвечать на простые запросы, открывать сайты и файлы, "
                    "искать в браузере, получать погоду и новости, а также выполнять "
                    "простые операции с файлами."
                ),
            )

        if self._is_weather_request(text):
            location_name = self._extract_weather_location(user_text)
            return AssistantDecision(
                decision_type="tool_call",
                tool_name="get_weather",
                tool_args={"location_name": location_name} if location_name else {},
            )

        if self._is_programming_news_request(text):
            return AssistantDecision(
                decision_type="tool_call",
                tool_name="get_programming_news",
                tool_args={"limit": 5},
            )

        create_with_text = self._extract_create_file_with_text(user_text)
        if create_with_text:
            return AssistantDecision(
                decision_type="tool_call",
                tool_name="create_file",
                tool_args=create_with_text,
                requires_confirmation=True,
            )

        rewrite_file = self._extract_rewrite_file(user_text)
        if rewrite_file:
            return AssistantDecision(
                decision_type="tool_call",
                tool_name="edit_file",
                tool_args=rewrite_file,
                requires_confirmation=True,
            )

        append_file = self._extract_append_file(user_text)
        if append_file:
            return AssistantDecision(
                decision_type="tool_call",
                tool_name="edit_file",
                tool_args=append_file,
                requires_confirmation=True,
            )

        replace_file_text = self._extract_replace_file_text(user_text)
        if replace_file_text:
            return AssistantDecision(
                decision_type="tool_call",
                tool_name="edit_file",
                tool_args=replace_file_text,
                requires_confirmation=True,
            )

        create_filename = self._extract_create_file_name(user_text)
        if create_filename:
            return AssistantDecision(
                decision_type="tool_call",
                tool_name="create_file",
                tool_args={"filename": create_filename, "content": ""},
                requires_confirmation=True,
            )

        delete_filename = self._extract_delete_file_name(user_text)
        if delete_filename:
            return AssistantDecision(
                decision_type="tool_call",
                tool_name="delete_file",
                tool_args={"filename": delete_filename},
                requires_confirmation=True,
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
                response_text="Скажите, что именно открыть.",
            )

        return AssistantDecision(
            decision_type="respond",
            response_text=f"Я получил сообщение: '{user_text}'.",
        )

    def _is_weather_request(self, text: str) -> bool:
        triggers = [
            "какая сегодня погода",
            "погода сегодня",
            "что по погоде",
            "какая погода",
            "weather",
        ]
        return any(trigger in text for trigger in triggers)

    def _extract_weather_location(self, text: str) -> str | None:
        match = re.search(r"(?:погода|weather)\s+(?:в|for)\s+(.+)$", text, re.IGNORECASE)
        if not match:
            return None
        location = match.group(1).strip(" .!?")
        return location or None

    def _is_programming_news_request(self, text: str) -> bool:
        triggers = [
            "какие новости программирования",
            "новости программирования",
            "новости python",
            "новости разработки",
            "tech news",
        ]
        return any(trigger in text for trigger in triggers)

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

    def _extract_create_file_with_text(self, text: str) -> dict[str, str] | None:
        match = self.CREATE_FILE_WITH_TEXT_PATTERN.search(text)
        if match:
            return {
                "filename": match.group(1).strip(),
                "content": match.group(2).strip(),
            }
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

    def _extract_append_file(self, text: str) -> dict[str, str] | None:
        match = self.APPEND_FILE_PATTERN.search(text)
        if match:
            return {
                "filename": match.group(1).strip(),
                "mode": "append",
                "content": match.group(2).strip(),
            }
        return None

    def _extract_replace_file_text(self, text: str) -> dict[str, str] | None:
        match = self.REPLACE_FILE_TEXT_PATTERN.search(text)
        if match:
            return {
                "filename": match.group(1).strip(),
                "mode": "replace_text",
                "old_text": match.group(2).strip(),
                "new_text": match.group(3).strip(),
            }
        return None

    def _extract_rewrite_file(self, text: str) -> dict[str, str] | None:
        match = self.REWRITE_FILE_PATTERN.search(text)
        if match:
            return {
                "filename": match.group(1).strip(),
                "mode": "replace_all",
                "content": match.group(2).strip(),
            }
        return None

    def _extract_delete_file_name(self, text: str) -> str | None:
        match = self.DELETE_FILE_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        return None
