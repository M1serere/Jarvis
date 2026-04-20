from __future__ import annotations

import json

import requests
from pydantic import ValidationError

from brain.adapters.base import BaseBrainAdapter
from core.config import (
    OLLAMA_BASE_URL,
    OLLAMA_KEEP_ALIVE,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
)
from core.models import AssistantDecision


class OllamaBrainAdapter(BaseBrainAdapter):
    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        timeout: int = OLLAMA_TIMEOUT_SECONDS,
        keep_alive: str = OLLAMA_KEEP_ALIVE,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.keep_alive = keep_alive

    def decide(
        self,
        user_text: str,
        conversation_context: list[dict[str, str]],
        system_prompt: str,
        available_tools: list[dict[str, str]] | None = None,
    ) -> AssistantDecision:
        prompt = self._build_prompt(
            user_text=user_text,
            conversation_context=conversation_context,
            available_tools=available_tools or [],
        )

        schema = AssistantDecision.model_json_schema()

        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": prompt,
            "format": schema,
            "stream": False,
            "keep_alive": self.keep_alive,
        }

        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()

        data = response.json()
        raw_response = data.get("response", "").strip()

        if not raw_response:
            return AssistantDecision(
                decision_type="respond",
                response_text="\u042f \u043d\u0435 \u0441\u043c\u043e\u0433 \u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043e\u0442\u0432\u0435\u0442 \u0447\u0435\u0440\u0435\u0437 Ollama.",
            )

        try:
            try:
                parsed = json.loads(raw_response)
            except json.JSONDecodeError:
                # fallback: extract a JSON object from a text response
                import re

                match = re.search(r"\{.*\}", raw_response, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                else:
                    raise
            return AssistantDecision.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError):
            return AssistantDecision(
                decision_type="respond",
                response_text=(
                    "\u042f \u043f\u043e\u043b\u0443\u0447\u0438\u043b \u043d\u0435\u043a\u043e\u0440\u0440\u0435\u043a\u0442\u043d\u044b\u0439 \u043e\u0442\u0432\u0435\u0442 \u043e\u0442 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u043e\u0439 \u043c\u043e\u0434\u0435\u043b\u0438. "
                    "\u041f\u0440\u043e\u0432\u0435\u0440\u044c \u043f\u0440\u043e\u043c\u043f\u0442 \u0438\u043b\u0438 \u0432\u044b\u0431\u0435\u0440\u0438 \u0434\u0440\u0443\u0433\u0443\u044e \u043c\u043e\u0434\u0435\u043b\u044c."
                ),
            )

    def _build_prompt(
        self,
        user_text: str,
        conversation_context: list[dict[str, str]],
        available_tools: list[dict[str, str]],
    ) -> str:
        recent_context = conversation_context[-8:]

        user_name = ""
        if hasattr(self, "user_profile") and self.user_profile:
            name = self.user_profile.get_name()
            if name:
                user_name = f"User name: {name}"

        context_lines: list[str] = []
        for item in recent_context:
            role = item.get("role", "unknown")
            text = item.get("text", "")
            context_lines.append(f"{role}: {text}")

        tools_lines: list[str] = []
        for tool in available_tools:
            name = tool.get("name", "")
            description = tool.get("description", "")
            risk_level = tool.get("risk_level", "safe")
            tools_lines.append(
                f"- {name}: {description} (risk_level={risk_level})"
            )

        tools_block = "\n".join(tools_lines) if tools_lines else "- no tools available"
        context_block = "\n".join(context_lines) if context_lines else "no prior context"
        user_block = f"\nKnown user name:\n{user_name}\n" if user_name else ""

        return f"""
You are the routing brain for a personal assistant called Jarvis.

Your task is to return ONLY one JSON object matching the provided schema.

Available tools:
{tools_block}

Recent conversation:
{context_block}
{user_block}

Current user message:
{user_text}

Routing rules:
1. If a normal conversational answer is enough, return:
   {{
     "decision_type": "respond",
     "response_text": "..."
   }}

2. If a tool is needed, return:
   {{
     "decision_type": "tool_call",
     "response_text": "",
     "tool_name": "exact_tool_name",
     "tool_args": {{}},
     "requires_confirmation": true_or_false
   }}

3. Use only tool names from the available tools list.

4. Mark requires_confirmation=true for file-changing operations such as:
   - create_file
   - edit_file

5. Mark requires_confirmation=false for clearly safe operations such as:
   - open_url
   - browser_search
   - get_weather
   - get_programming_news
   - open_file
   - window_control

6. If the user asks to create a file with text, use create_file with:
   {{
     "filename": "...",
     "content": "..."
   }}

   If the user asks for a file for a specific program, also pass:
   {{
     "file_type": "txt" | "docx" | "xlsx" | "pptx"
   }}

   Examples:
   - Word -> "file_type": "docx"
   - Excel -> "file_type": "xlsx"
   - PowerPoint -> "file_type": "pptx"

   Files are created on the Desktop by default, so do not ask the tool to use the workspace unless the user explicitly asked for another location.

7. If the user asks to append text, replace text, or fully rewrite a file, use edit_file with:
   mode = "append" | "replace_text" | "replace_all"

8. Do not invent tools that are not listed.

9. If the user asks about weather for a specific city or country, pass it to get_weather as:
   {{
     "location_name": "city name"
   }}

10. If the user asks to minimize, restore, or manage all windows in Windows, use window_control with:
   {{
     "action": "minimize_all" | "restore_all"
   }}

Return only valid JSON.
""".strip()
