from __future__ import annotations

import re

from brain.adapters.base import BaseBrainAdapter
from core.models import AssistantDecision


class MockBrainAdapter(BaseBrainAdapter):
    URL_PATTERN = re.compile(
        r"(https?://[^\s]+|[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)"
    )

    CREATE_FILE_WITH_TEXT_PATTERN = re.compile(
        r"СЃРѕР·РґР°Р№ С„Р°Р№Р»\s+([^\s]+)\s+СЃ С‚РµРєСЃС‚РѕРј\s+(.+)",
        re.IGNORECASE,
    )

    CREATE_FILE_PATTERN = re.compile(
        r"СЃРѕР·РґР°Р№ С„Р°Р№Р»\s+([^\s]+)",
        re.IGNORECASE,
    )

    OPEN_FILE_PATTERN = re.compile(
        r"РѕС‚РєСЂРѕР№ С„Р°Р№Р»\s+([^\s]+)",
        re.IGNORECASE,
    )

    APPEND_FILE_PATTERN = re.compile(
        r"РґРѕР±Р°РІСЊ РІ С„Р°Р№Р»\s+([^\s]+)\s+С‚РµРєСЃС‚\s+(.+)",
        re.IGNORECASE,
    )

    REPLACE_FILE_TEXT_PATTERN = re.compile(
        r"Р·Р°РјРµРЅРё РІ С„Р°Р№Р»Рµ\s+([^\s]+)\s+(.+)\s+РЅР°\s+(.+)",
        re.IGNORECASE,
    )

    REWRITE_FILE_PATTERN = re.compile(
        r"РёР·РјРµРЅРё С„Р°Р№Р»\s+([^\s]+)\s+РЅР° С‚РµРєСЃС‚\s+(.+)",
        re.IGNORECASE,
    )

    DELETE_FILE_PATTERN = re.compile(
        r"СѓРґР°Р»Рё С„Р°Р№Р»\s+([^\s]+)",
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

        if "РїСЂРёРІРµС‚" in text:
            return AssistantDecision(
                decision_type="respond",
                response_text="РџСЂРёРІРµС‚. РЇ РЅР° СЃРІСЏР·Рё.",
            )

        if "РєР°Рє РґРµР»Р°" in text:
            return AssistantDecision(
                decision_type="respond",
                response_text=(
                    "Р Р°Р±РѕС‚Р°СЋ СЃС‚Р°Р±РёР»СЊРЅРѕ. РЎРµР№С‡Р°СЃ СЌС‚Рѕ mock-СЂРµР¶РёРј."
                ),
            )

        if "С‡С‚Рѕ С‚С‹ СѓРјРµРµС€СЊ" in text:
            return AssistantDecision(
                decision_type="respond",
                response_text=(
                    "РЎРµР№С‡Р°СЃ СЏ СѓРјРµСЋ РѕС‚РІРµС‡Р°С‚СЊ С‚РµРєСЃС‚РѕРј, РѕС‚РєСЂС‹РІР°С‚СЊ СЃР°Р№С‚С‹, РёСЃРєР°С‚СЊ РІ Google, "
                    "СЃРѕР·РґР°РІР°С‚СЊ С„Р°Р№Р»С‹, С‡РёС‚Р°С‚СЊ С„Р°Р№Р»С‹, РёР·РјРµРЅСЏС‚СЊ С„Р°Р№Р»С‹ РІ СЂР°Р±РѕС‡РµР№ РїР°РїРєРµ, "
                    "РїРѕР»СѓС‡Р°С‚СЊ РїРѕРіРѕРґСѓ Рё СЃРІРµР¶РёРµ РЅРѕРІРѕСЃС‚Рё РїСЂРѕРіСЂР°РјРјРёСЂРѕРІР°РЅРёСЏ."
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

        if any(phrase in text for phrase in ["РѕС‚РєСЂРѕР№ СЃР°Р№С‚", "РѕС‚РєСЂРѕР№", "open"]):
            url = self._extract_url(user_text)
            if url:
                return AssistantDecision(
                    decision_type="tool_call",
                    tool_name="open_url",
                    tool_args={"url": url},
                )

            return AssistantDecision(
                decision_type="respond",
                response_text="РЇ РїРѕРЅСЏР», С‡С‚Рѕ РЅСѓР¶РЅРѕ РѕС‚РєСЂС‹С‚СЊ СЃР°Р№С‚, РЅРѕ РЅРµ СѓРІРёРґРµР» Р°РґСЂРµСЃ.",
            )

        return AssistantDecision(
            decision_type="respond",
            response_text=f"РЇ РїРѕР»СѓС‡РёР» СЃРѕРѕР±С‰РµРЅРёРµ: '{user_text}'.",
        )

    def _is_weather_request(self, text: str) -> bool:
        triggers = [
            "РєР°РєР°СЏ СЃРµРіРѕРґРЅСЏ РїРѕРіРѕРґР°",
            "РїРѕРіРѕРґР° СЃРµРіРѕРґРЅСЏ",
            "С‡С‚Рѕ РїРѕ РїРѕРіРѕРґРµ",
            "РєР°РєР°СЏ РїРѕРіРѕРґР°",
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
            "РєР°РєРёРµ РЅРѕРІРѕСЃС‚Рё РїСЂРѕРіСЂР°РјРјРёСЂРѕРІР°РЅРёСЏ",
            "РЅРѕРІРѕСЃС‚Рё РїСЂРѕРіСЂР°РјРјРёСЂРѕРІР°РЅРёСЏ",
            "РЅРѕРІРѕСЃС‚Рё python",
            "РЅРѕРІРѕСЃС‚Рё СЂР°Р·СЂР°Р±РѕС‚РєРё",
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
            "РЅР°Р№РґРё РІ РіСѓРіР»Рµ ",
            "РїРѕРёС‰Рё РІ РіСѓРіР»Рµ ",
            "РЅР°Р№РґРё РІ google ",
            "РїРѕРёС‰Рё РІ google ",
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
