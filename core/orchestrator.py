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

        decision = self.brain.decide(user_message)
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
            if not decision.tool_name or not self.tools.has_tool(decision.tool_name):
                response_text = "Инструмент пока недоступен."
                self.logger.warning("Tool not found: %s", decision.tool_name)
            else:
                result = self.tools.execute(decision.tool_name, decision.tool_args)
                response_text = result
        else:
            response_text = decision.response_text

        self.memory.add_assistant_message(response_text)
        self.logger.info("Assistant response: %s", response_text)

        return OrchestratorResponse(
            response_text=response_text,
            raw_decision=decision,
            approved=True,
        )