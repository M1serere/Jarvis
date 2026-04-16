from __future__ import annotations

from brain.brain import Brain
from core.logger import setup_logger
from core.models import OrchestratorResponse, UserMessage
from memory.session_memory import SessionMemory
from safety.guard import SafetyGuard
from tools.registry import ToolRegistry

from core.models import OrchestratorResponse, UserMessage, empty_decision

from memory.persistent_memory import PersistentMemory
from memory.user_profile import UserProfile
from memory.references import ReferenceResolver
from core.config import BASE_DIR

from memory.facts_memory import FactsMemory

class JarvisOrchestrator:
    CONFIRM_WORDS = {"да", "ага", "подтверждаю", "yes", "y"}
    CANCEL_WORDS = {"нет", "отмена", "отменить", "no", "n"}

    def __init__(self) -> None:
        self.logger = setup_logger()
        self.brain = Brain()
        self.memory = SessionMemory()
        self.tools = ToolRegistry()
        self.safety = SafetyGuard(tool_registry=self.tools)

        self.logger.debug("Available tools: %s", self.tools.list_tools())

        self.persistent = PersistentMemory(BASE_DIR / "memory.json")
        self.profile = UserProfile(self.persistent)
        self.references = ReferenceResolver()

        self.facts_memory = FactsMemory(self.persistent)

    def handle_user_input(self, text: str) -> OrchestratorResponse:
        self.logger.info("Received user input: %s", text)

        user_message = UserMessage(text=text)
        self.memory.add_user_message(text)

        pending_action = self.memory.get_pending_action()
        if pending_action is not None:
            response = self._handle_confirmation_reply(user_message.text)
            self.memory.add_assistant_message(response.response_text)
            self.logger.debug("Assistant response: %s", response.response_text)
            return response

        context = self.memory.get_recent(limit=10)

        normalized_text = text.strip()
        lowered_text = normalized_text.lower()

        if lowered_text.startswith("зови меня "):
            name = normalized_text[len("зови меня "):].strip(" .!?")
            if name:
                self.profile.set_name(name)
                return OrchestratorResponse(
                    response_text=f"Хорошо. Теперь я буду обращаться к тебе: {name}.",
                    raw_decision=empty_decision(),
                    approved=True,
                )

        if lowered_text.startswith("моё имя "):
            name = normalized_text[len("моё имя "):].strip(" .!?")
            if name:
                self.profile.set_name(name)
                return OrchestratorResponse(
                    response_text=f"Запомнил. Твоё имя: {name}.",
                    raw_decision=empty_decision(),
                    approved=True,
                )

        if lowered_text in {
            "как меня зовут",
            "как меня зовут?",
            "кто я",
            "кто я?",
        }:
            name = self.profile.get_name()
            return OrchestratorResponse(
                response_text=f"Я обращаюсь к тебе как: {name}.",
                raw_decision=empty_decision(),
                approved=True,
            )

        if lowered_text.startswith("джарвис, запомни "):
            # fact = normalized_text[len("Джарвис, запомни "):].strip(" .!?")
            fact = normalized_text[len("Джарвис, запомни "):].strip(" .!?")
            if not fact:
                fact = normalized_text[len("джарвис, запомни "):].strip(" .!?")

            if fact.lower().startswith("что "):
                fact = fact[5:].strip()

            if not fact:
                fact = normalized_text[len("джарвис, запомни "):].strip(" .!?")

            if fact:
                self.facts_memory.add_fact(fact)
                return OrchestratorResponse(
                    response_text=f"Запомнил: {fact}.",
                    raw_decision=empty_decision(),
                    approved=True,
                )

        if lowered_text in {
            "джарвис, что ты обо мне помнишь",
            "что ты обо мне помнишь",
            "что ты помнишь обо мне",
        }:
            facts = self.facts_memory.get_facts()
            if not facts:
                return OrchestratorResponse(
                    response_text="Пока у меня нет сохранённых фактов о тебе.",
                    raw_decision=empty_decision(),
                    approved=True,
                )

            facts_text = "\n".join(f"{idx + 1}. {fact}" for idx, fact in enumerate(facts))
            return OrchestratorResponse(
                response_text=f"Вот что я помню о тебе:\n{facts_text}",
                raw_decision=empty_decision(),
                approved=True,
            )
        
        decision = self.brain.decide(
        user_text=user_message.text,
        conversation_context=context,
        available_tools=self.tools.list_tools(),
        )
        self.logger.info("Brain decision: %s", decision.model_dump_json())

        approved = self.safety.approve(decision)
        if not approved:
            response_text = self.safety.get_block_message(decision)

            if decision.requires_confirmation and decision.tool_name:
                self.memory.set_pending_action(
                    tool_name=decision.tool_name,
                    tool_args=decision.tool_args,
                    confirmation_message=response_text,
                )

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

    def _handle_confirmation_reply(self, text: str) -> OrchestratorResponse:
        normalized = text.strip().lower()
        pending_action = self.memory.get_pending_action()

        if pending_action is None:
            return OrchestratorResponse(
                response_text="Нет действия, ожидающего подтверждения.",
                raw_decision=empty_decision(),
                approved=False,
            )

        if normalized in self.CONFIRM_WORDS:
            self.logger.info(
                "Confirmation accepted for tool: %s with args=%s",
                pending_action.tool_name,
                pending_action.tool_args,
            )
            result = self._handle_tool_call(
                pending_action.tool_name,
                pending_action.tool_args,
            )
            self.memory.clear_pending_action()

            return OrchestratorResponse(
                response_text=result,
                raw_decision=empty_decision(),
                approved=True,
            )

        if normalized in self.CANCEL_WORDS:
            self.logger.info(
                "Confirmation declined for tool: %s",
                pending_action.tool_name,
            )
            self.memory.clear_pending_action()

            return OrchestratorResponse(
                response_text="Действие отменено.",
                raw_decision=empty_decision(),
                approved=False,
            )

        return OrchestratorResponse(
            response_text=(
                "Я жду подтверждение текущего действия. "
                "Ответь 'да' или 'нет'."
            ),
            raw_decision=empty_decision(),
            approved=False,
        )

    def _handle_tool_call(self, tool_name: str | None, tool_args: dict) -> str:
        
        tool_args = self.references.resolve(tool_args)

        if not tool_name:
            self.logger.warning("Tool call decision without tool name.")
            return "Инструмент не указан."

        if not self.tools.has_tool(tool_name):
            self.logger.warning("Tool not found: %s", tool_name)
            return f"Инструмент '{tool_name}' пока недоступен."
        
        if "filename" in tool_args:
            self.references.remember_file(tool_args["filename"])
            self.memory.set_last_file(tool_args["filename"])
        
        try:
            self.logger.info("Executing tool: %s with args=%s", tool_name, tool_args)
            result = self.tools.execute(tool_name, tool_args)
            self.logger.info("Tool result: %s", result)
            return result
        except Exception as exc:
            self.logger.exception("Tool execution failed: %s", tool_name)
            return f"Во время выполнения инструмента '{tool_name}' произошла ошибка: {exc}"