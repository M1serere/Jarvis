from __future__ import annotations
from urllib import response

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

from core.models import OrchestratorResponse, UserMessage, empty_decision

class JarvisOrchestrator:
    CONFIRM_WORDS = {"да", "ага", "подтверждаю", "yes", "y"}
    CANCEL_WORDS = {"нет", "отмена", "отменить", "no", "n"}

    MUSIC_YOUTUBE_WORDS = {"ютуб", "youtube", "на ютубе", "в ютубе"}
    MUSIC_YANDEX_WORDS = {
        "яндекс",
        "яндекс музыка",
        "yandex",
        "yandex music",
        "в яндекс музыке",
        "на яндекс музыке",
    }

    def __init__(self, status_ui=None) -> None:
        self.logger = setup_logger()
        self.status_ui = status_ui
        self.brain = Brain()
        self.memory = SessionMemory()
        self.tools = ToolRegistry()
        self.safety = SafetyGuard(tool_registry=self.tools)

        self.logger.debug("Available tools: %s", self.tools.list_tools())

        self.persistent = PersistentMemory(BASE_DIR / "memory.json")
        self.profile = UserProfile(self.persistent)
        self.references = ReferenceResolver()

        self.facts_memory = FactsMemory(self.persistent)

    def _set_status(self, status: str, detail: str = "") -> None:
            if self.status_ui is not None:
                self.status_ui.set_status(status, detail)

    def handle_user_input(self, text: str) -> OrchestratorResponse:
        self._set_status("Думает", "Анализ команды")
        self.logger.info("Received user input: %s", text)
        self.logger.info("User said: %s", text)

        user_message = UserMessage(text=text)
        self.memory.add_user_message(text)


        pending_action = self.memory.get_pending_action()
        if pending_action is not None:
            response = self._handle_confirmation_reply(user_message.text)
            self.memory.add_assistant_message(response.response_text)
            self.logger.debug("Assistant response: %s", response.response_text)
            return response

        pending_question = self.memory.get_pending_question()
        if pending_question is not None:
            response = self._handle_pending_question_reply(user_message.text)
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
        
        music_response = self._handle_explicit_music_request(text)
        if music_response is not None:
            self.memory.add_assistant_message(music_response.response_text)
            self.logger.debug("Assistant response: %s", music_response.response_text)
            return music_response

        decision = self.brain.decide(
            user_text=user_message.text,
            conversation_context=context,
            available_tools=self.tools.list_tools(),
        )
        self.logger.info("Brain decision: %s", decision.model_dump_json())
        
        self.logger.info("Assistant understood: %s", decision.model_dump_json())
        if decision.decision_type == "tool_call":
            self.logger.info(
                "Assistant selected action: %s | args=%s",
                decision.tool_name,
                decision.tool_args,
            )

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
            self._set_status("Готов", "Ожидание подтверждения")
            
            return OrchestratorResponse(
                response_text=response_text,
                raw_decision=decision,
                approved=False,
            )


        #self._set_status("Выполняет", f"Инструмент: {decision.tool_name}")

        if decision.decision_type == "tool_call":
            self._set_status("Выполняет", f"Инструмент: {decision.tool_name}")
            response_text = self._handle_tool_call(decision.tool_name, decision.tool_args)
        else:
            response_text = decision.response_text

        self.memory.add_assistant_message(response_text)
        self.logger.debug("Assistant response: %s", response_text)
        self._set_status("Готов", "Ожидание команды")

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
            self._set_status("Выполняет", f"Подтверждено: {pending_action.tool_name}")
            result = self._handle_tool_call(
                pending_action.tool_name,
                pending_action.tool_args,
            )
            self.memory.clear_pending_action()
            self._set_status("Готов", "Ожидание команды")

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
            self._set_status("Готов", "Действие отменено")

            return OrchestratorResponse(
                response_text="Действие отменено.",
                raw_decision=empty_decision(),
                approved=False,
            )
        self._set_status("Готов", "Ожидание подтверждения")
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


    def _handle_explicit_music_request(self, text: str) -> OrchestratorResponse | None:
        lowered = text.strip().lower()

        play_music_triggers = [
            "включи музыку",
            "запусти музыку",
            "поставь музыку",
        ]
        stop_music_triggers = [
            "выключи музыку",
            "останови музыку",
            "поставь на паузу музыку",
            "пауза",
            "поставь на паузу",
        ]

        if any(trigger in lowered for trigger in stop_music_triggers):
            result = self._handle_tool_call(
                "music_control",
                {"action": "pause", "source": ""},
            )
            return OrchestratorResponse(
                response_text=result,
                raw_decision=empty_decision(),
                approved=True,
            )

        if any(trigger in lowered for trigger in play_music_triggers):
            if self._is_youtube_source(lowered):
                result = self._handle_tool_call(
                    "music_control",
                    {"action": "play", "source": "youtube"},
                )
                return OrchestratorResponse(
                    response_text=result,
                    raw_decision=empty_decision(),
                    approved=True,
                )

            if self._is_yandex_source(lowered):
                result = self._handle_tool_call(
                    "music_control",
                    {"action": "play", "source": "yandex_music"},
                )
                return OrchestratorResponse(
                    response_text=result,
                    raw_decision=empty_decision(),
                    approved=True,
                )

            self.memory.set_pending_question("music_source", {"action": "play"})
            return OrchestratorResponse(
                response_text="Где включить музыку: на YouTube или в Яндекс Музыке?",
                raw_decision=empty_decision(),
                approved=True,
            )

        return None


    def _handle_pending_question_reply(self, text: str) -> OrchestratorResponse:
        pending_question = self.memory.get_pending_question()
        normalized = text.strip().lower()

        if pending_question is None:
            return OrchestratorResponse(
                response_text="У меня нет активного уточняющего вопроса.",
                raw_decision=empty_decision(),
                approved=False,
            )

        if pending_question.question_type == "music_source":
            if self._is_youtube_source(normalized):
                self.memory.clear_pending_question()
                result = self._handle_tool_call(
                    "music_control",
                    {"action": "play", "source": "youtube"},
                )
                return OrchestratorResponse(
                    response_text=result,
                    raw_decision=empty_decision(),
                    approved=True,
                )

            if self._is_yandex_source(normalized):
                self.memory.clear_pending_question()
                result = self._handle_tool_call(
                    "music_control",
                    {"action": "play", "source": "yandex_music"},
                )
                return OrchestratorResponse(
                    response_text=result,
                    raw_decision=empty_decision(),
                    approved=True,
                )

            return OrchestratorResponse(
                response_text="Я жду ответ: YouTube или Яндекс Музыка.",
                raw_decision=empty_decision(),
                approved=False,
            )

        self.memory.clear_pending_question()
        return OrchestratorResponse(
            response_text="Неизвестный тип уточняющего вопроса.",
            raw_decision=empty_decision(),
            approved=False,
        )


    def _is_youtube_source(self, text: str) -> bool:
        return any(word in text for word in self.MUSIC_YOUTUBE_WORDS)


    def _is_yandex_source(self, text: str) -> bool:
        return any(word in text for word in self.MUSIC_YANDEX_WORDS)
    
    