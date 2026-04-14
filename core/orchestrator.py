from __future__ import annotations

from brain.brain import Brain
from core.logger import setup_logger
from core.models import OrchestratorResponse, UserMessage
from memory.session_memory import SessionMemory
from safety.guard import SafetyGuard
from tools.registry import ToolRegistry


class JarvisOrchestrator:
    def __init__(self) -> None:
        self.logger = setup_logger()
        self.brain = Brain()
        self.memory = SessionMemory()
        self.safety = SafetyGuard()
        self.tools = ToolRegistry()

    def handle_user_input(self, text: str) -> OrchestratorResponse:
        self.logger.info("Received user input: %s", text)

        user_message = UserMessage(text=text)
        self.memory.add_user_message(text)

        context = self.memory.get_recent(limit=10)

        decision = self.brain.decide(
            user_text=user_message.text,
            conversation_context=context,
        )
        self.logger.info("Brain decision: %s", decision.model_dump_json())

        approved = self.safety.approve(decision)
        if not approved:
            response_text = "Действие не прошло проверку безопасности."
            self.memory.add_assistant_message(response_text)
            self.logger.warning("Decision blocked by safety guard.")

            return OrchestratorResponse(
                response_text=response_text,
                raw_decision=decision,
                approved=False,
            )

        if decision.decision_type == "tool_call":
            response_text = self._handle_tool_call(decision.tool_name, decision.tool_args)
        else:
            response_text = decision.response_text

        self.memory.add_assistant_message(response_text)
        self.logger.debug("Assistant response: %s", response_text)

        return OrchestratorResponse(
            response_text=response_text,
            raw_decision=decision,
            approved=True,
        )

    def _handle_tool_call(self, tool_name: str | None, tool_args: dict) -> str:
        if not tool_name:
            self.logger.warning("Tool call decision without tool name.")
            return "Инструмент не указан."

        if not self.tools.has_tool(tool_name):
            self.logger.warning("Tool not found: %s", tool_name)
            return f"Инструмент '{tool_name}' пока недоступен."

        try:
            self.logger.info("Executing tool: %s with args=%s", tool_name, tool_args)
            result = self.tools.execute(tool_name, tool_args)
            self.logger.info("Tool result: %s", result)
            return result
        except Exception as exc:
            self.logger.exception("Tool execution failed: %s", tool_name)
            return f"Во время выполнения инструмента '{tool_name}' произошла ошибка: {exc}"