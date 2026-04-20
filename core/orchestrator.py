from __future__ import annotations

import re

from brain.brain import Brain
from core.config import BASE_DIR
from core.logger import setup_logger
from core.models import OrchestratorResponse, UserMessage, empty_decision
from memory.facts_memory import FactsMemory
from memory.session_memory import NewsItem
from memory.persistent_memory import PersistentMemory
from memory.references import ReferenceResolver
from memory.session_memory import SessionMemory
from memory.user_profile import UserProfile
from safety.guard import SafetyGuard
from safety.messages import build_confirmation_message
from services.browser_window_service import BrowserWindowService
from services.habr_news_service import HABR_DAILY_NEWS_URL, HabrNewsService
from services.http_client import HttpClient
from tools.registry import ToolRegistry


class JarvisOrchestrator:
    CONFIRM_WORDS = {"да", "ага", "подтверждаю", "yes", "y"}
    CANCEL_WORDS = {"нет", "отмена", "отменить", "no", "n"}

    MUSIC_YOUTUBE_WORDS = {"ютуб", "youtube", "на ютубе", "в ютубе"}

    def __init__(self, status_ui=None, work_time_provider=None) -> None:
        self.logger = setup_logger()
        self.status_ui = status_ui
        self.work_time_provider = work_time_provider
        self.brain = Brain()
        self.memory = SessionMemory()
        self.tools = ToolRegistry()
        self.safety = SafetyGuard(tool_registry=self.tools)

        self.logger.debug("Available tools: %s", self.tools.list_tools())

        self.persistent = PersistentMemory(BASE_DIR / "memory.json")
        self.profile = UserProfile(self.persistent)
        self.references = ReferenceResolver()
        self.facts_memory = FactsMemory(self.persistent)
        self.browser_window = BrowserWindowService()
        self.habr_news = HabrNewsService(http_client=HttpClient())

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
            fact = normalized_text[len("Джарвис, запомни "):].strip(" .!?")
            if not fact:
                fact = normalized_text[len("джарвис, запомни "):].strip(" .!?")

            if fact.lower().startswith("что "):
                fact = fact[4:].strip()

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

        goodbye_response = self._handle_goodbye_request(lowered_text)
        if goodbye_response is not None:
            self.memory.add_assistant_message(goodbye_response.response_text)
            self.logger.debug("Assistant response: %s", goodbye_response.response_text)
            return goodbye_response

        work_time_response = self._handle_work_time_request(lowered_text)
        if work_time_response is not None:
            return work_time_response

        window_response = self._handle_window_request(lowered_text)
        if window_response is not None:
            self.memory.add_assistant_message(window_response.response_text)
            self.logger.debug("Assistant response: %s", window_response.response_text)
            return window_response

        news_response = self._handle_habr_news_request(text)
        if news_response is not None:
            self.memory.add_assistant_message(news_response.response_text)
            self.logger.debug("Assistant response: %s", news_response.response_text)
            return news_response

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
            "продолжи музыку",
            "воспроизведи музыку",
        ]
        pause_music_triggers = [
            "выключи музыку",
            "останови музыку",
            "поставь на паузу музыку",
            "пауза",
            "поставь на паузу",
            "останови видео",
            "пауза музыка",
        ]
        next_music_triggers = [
            "следующее видео",
            "включи следующее видео",
            "следующий трек",
            "следующая песня",
            "дальше",
            "переключи видео",
            "переключи трек",
        ]
        volume_down_triggers = [
            "сделай потише",
            "потише",
            "уменьши громкость",
            "убавь громкость",
            "громкость ниже",
        ]
        volume_up_triggers = [
            "сделай погромче",
            "погромче",
            "увеличь громкость",
            "добавь громкость",
            "громкость выше",
        ]

        volume_value = self._extract_volume_value(lowered)
        if volume_value is not None:
            result = self._handle_tool_call(
                "music_control",
                {"action": "set_volume", "value": volume_value, "source": ""},
            )
            return OrchestratorResponse(
                response_text=result,
                raw_decision=empty_decision(),
                approved=True,
            )

        if any(trigger in lowered for trigger in volume_down_triggers):
            result = self._handle_tool_call(
                "music_control",
                {"action": "volume_down", "source": ""},
            )
            return OrchestratorResponse(
                response_text=result,
                raw_decision=empty_decision(),
                approved=True,
            )

        if any(trigger in lowered for trigger in volume_up_triggers):
            result = self._handle_tool_call(
                "music_control",
                {"action": "volume_up", "source": ""},
            )
            return OrchestratorResponse(
                response_text=result,
                raw_decision=empty_decision(),
                approved=True,
            )

        if any(trigger in lowered for trigger in next_music_triggers):
            result = self._handle_tool_call(
                "music_control",
                {"action": "next", "source": ""},
            )
            return OrchestratorResponse(
                response_text=result,
                raw_decision=empty_decision(),
                approved=True,
            )

        if any(trigger in lowered for trigger in pause_music_triggers):
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
            result = self._handle_tool_call(
                "music_control",
                {"action": "play", "source": "youtube"},
            )
            return OrchestratorResponse(
                response_text=result,
                raw_decision=empty_decision(),
                approved=True,
            )

        return None

    def _handle_habr_news_request(self, text: str) -> OrchestratorResponse | None:
        cleaned_text = self._normalize_phrase(text)

        show_news_triggers = {
            "покажи новости",
            "покажи новость",
            "покажи новости на хабре",
            "открой новости",
            "открой новости на хабре",
            "новости",
            "новости хабр",
            "новости на хабре",
            "покажи свежие новости",
        }
        next_news_triggers = {
            "дальше",
            "следующая",
            "следующая новость",
            "покажи следующую новость",
        }
        open_news_triggers = {
            "это интересно",
            "открой",
            "открой эту",
            "открой эту новость",
            "открой новость",
        }

        if cleaned_text in show_news_triggers:
            return self._start_habr_news_browse()

        if cleaned_text in next_news_triggers:
            return self._speak_next_habr_news()

        if cleaned_text in open_news_triggers:
            return self._open_current_habr_news()

        return None

    def _start_habr_news_browse(self) -> OrchestratorResponse:
        try:
            entries = self.habr_news.get_daily_news(limit=10)
        except Exception as exc:
            self.logger.exception("Failed to fetch Habr news.")
            return OrchestratorResponse(
                response_text=f"Не удалось получить новости с Habr: {exc}",
                raw_decision=empty_decision(),
                approved=False,
            )

        if not entries:
            return OrchestratorResponse(
                response_text="Не удалось найти новости на Habr.",
                raw_decision=empty_decision(),
                approved=False,
            )

        self.memory.set_news_items(
            [NewsItem(title=entry.title, url=entry.url) for entry in entries]
        )
        self._handle_tool_call("open_url", {"url": HABR_DAILY_NEWS_URL})
        current_item = self.memory.get_current_news()

        if current_item is None:
            return OrchestratorResponse(
                response_text="Не удалось подготовить список новостей.",
                raw_decision=empty_decision(),
                approved=False,
            )

        self.browser_window.scroll_to_text(
            current_item.title,
            title_hints=["habr", "chrome", "edge", "firefox", "opera", "yandex"],
        )
        return OrchestratorResponse(
            response_text=f"Вот сегодняшние новости. {current_item.title}.",
            raw_decision=empty_decision(),
            approved=True,
        )

    def _speak_next_habr_news(self) -> OrchestratorResponse:
        if not self.memory.has_news_items():
            return OrchestratorResponse(
                response_text="Сначала скажи 'покажи новости'.",
                raw_decision=empty_decision(),
                approved=False,
            )

        current_before_move = self.memory.get_current_news()
        next_item = self.memory.move_to_next_news()

        if next_item is None:
            return OrchestratorResponse(
                response_text="Список новостей сейчас недоступен.",
                raw_decision=empty_decision(),
                approved=False,
            )

        if current_before_move is not None and current_before_move.url == next_item.url:
            self.browser_window.scroll_to_text(
                next_item.title,
                title_hints=["habr", "chrome", "edge", "firefox", "opera", "yandex"],
            )
            return OrchestratorResponse(
                response_text=f"Это последняя новость на сегодня: {next_item.title}.",
                raw_decision=empty_decision(),
                approved=True,
            )

        self.browser_window.scroll_to_text(
            next_item.title,
            title_hints=["habr", "chrome", "edge", "firefox", "opera", "yandex"],
        )
        return OrchestratorResponse(
            response_text=next_item.title,
            raw_decision=empty_decision(),
            approved=True,
        )

    def _open_current_habr_news(self) -> OrchestratorResponse:
        current_item = self.memory.get_current_news()
        if current_item is None:
            return OrchestratorResponse(
                response_text="Сначала скажи 'покажи новости', чтобы я открыл список.",
                raw_decision=empty_decision(),
                approved=False,
            )

        self._handle_tool_call("open_url", {"url": current_item.url})
        self.browser_window.bring_to_front(
            title_hints=["habr", "chrome", "edge", "firefox", "opera", "yandex"],
        )
        self.memory.clear_news_items()
        return OrchestratorResponse(
            response_text="Открываю. Приятного чтения.",
            raw_decision=empty_decision(),
            approved=True,
            keep_awake=False,
        )

    def _extract_volume_value(self, text: str) -> int | None:
        patterns = [
            r"громкость\s+(\d{1,3})",
            r"поставь громкость\s+на\s+(\d{1,3})",
            r"установи громкость\s+на\s+(\d{1,3})",
            r"сделай громкость\s+(\d{1,3})",
            r"volume\s+(\d{1,3})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                return max(0, min(100, value))

        return None

    def _handle_work_time_request(self, lowered_text: str) -> OrchestratorResponse | None:
        work_time_triggers = {
            "сколько я работаю",
            "сколько я уже работаю",
            "сколько времени я работаю",
            "сколько времени я уже работаю",
            "как долго я работаю",
            "как долго я уже работаю",
        }

        cleaned_text = lowered_text.strip(" .!?")
        if cleaned_text not in work_time_triggers:
            return None

        if self.work_time_provider is None:
            return OrchestratorResponse(
                response_text="Я пока не могу определить, сколько времени вы работаете.",
                raw_decision=empty_decision(),
                approved=True,
            )

        elapsed_seconds = max(0, int(self.work_time_provider()))
        response_text = f"Вы работаете {self._format_work_duration(elapsed_seconds)}."
        return OrchestratorResponse(
            response_text=response_text,
            raw_decision=empty_decision(),
            approved=True,
        )

    def _handle_goodbye_request(self, lowered_text: str) -> OrchestratorResponse | None:
        cleaned_text = re.sub(r"\s+", " ", lowered_text.strip(" .!?"))
        goodbye_triggers = {
            "джарвис, хорошая работа до встречи",
            "джарвис хорошая работа до встречи",
        }

        if cleaned_text not in goodbye_triggers:
            return None

        self.memory.set_pending_question("power_action")
        return OrchestratorResponse(
            response_text="Спасибо. Перевести ноутбук в сон или выключить его?",
            raw_decision=empty_decision(),
            approved=True,
        )

    def _handle_window_request(self, lowered_text: str) -> OrchestratorResponse | None:
        cleaned_text = lowered_text.strip(" .!?")

        minimize_triggers = {
            "сверни все окна",
            "сверни окна",
            "сверни всё",
            "сверни все",
            "покажи рабочий стол",
        }
        restore_triggers = {
            "разверни все окна",
            "разверни окна",
            "разверни всё",
            "разверни все",
            "восстанови все окна",
            "верни все окна",
        }

        if cleaned_text in minimize_triggers:
            result = self._handle_tool_call(
                "window_control",
                {"action": "minimize_all"},
            )
            return OrchestratorResponse(
                response_text=result,
                raw_decision=empty_decision(),
                approved=True,
            )

        if cleaned_text in restore_triggers:
            result = self._handle_tool_call(
                "window_control",
                {"action": "restore_all"},
            )
            return OrchestratorResponse(
                response_text=result,
                raw_decision=empty_decision(),
                approved=True,
            )

        return None

    def _format_work_duration(self, elapsed_seconds: int) -> str:
        total_minutes = max(0, elapsed_seconds // 60)
        hours, minutes = divmod(total_minutes, 60)

        if hours == 0:
            if minutes == 0:
                return "меньше минуты"
            return f"{minutes} {self._pluralize(minutes, 'минуту', 'минуты', 'минут')}"

        if minutes == 0:
            return f"{hours} {self._pluralize(hours, 'час', 'часа', 'часов')}"

        return (
            f"{hours} {self._pluralize(hours, 'час', 'часа', 'часов')} "
            f"{minutes} {self._pluralize(minutes, 'минуту', 'минуты', 'минут')}"
        )

    def _pluralize(self, value: int, one: str, few: str, many: str) -> str:
        last_two = value % 100
        last_one = value % 10

        if 11 <= last_two <= 14:
            return many
        if last_one == 1:
            return one
        if 2 <= last_one <= 4:
            return few
        return many

    def _handle_pending_question_reply(self, text: str) -> OrchestratorResponse:
        pending_question = self.memory.get_pending_question()

        if pending_question is None:
            return OrchestratorResponse(
                response_text="У меня нет активного уточняющего вопроса.",
                raw_decision=empty_decision(),
                approved=False,
            )

        if pending_question.question_type == "music_source":
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

        if pending_question.question_type == "power_action":
            normalized = re.sub(r"\s+", " ", text.strip().lower().strip(" .!?"))

            if normalized in self.CANCEL_WORDS:
                self.memory.clear_pending_question()
                return OrchestratorResponse(
                    response_text="Хорошо, отменяю завершение работы.",
                    raw_decision=empty_decision(),
                    approved=False,
                )

            action = None
            if "сон" in normalized:
                action = "sleep"
            elif "выключ" in normalized:
                action = "shutdown"

            if action is None:
                return OrchestratorResponse(
                    response_text="Уточни, пожалуйста: перевести ноутбук в сон или выключить?",
                    raw_decision=empty_decision(),
                    approved=False,
                )

            self.memory.clear_pending_question()
            confirmation_message = build_confirmation_message(
                "system_power",
                {"action": action},
            )
            self.memory.set_pending_action(
                tool_name="system_power",
                tool_args={"action": action},
                confirmation_message=confirmation_message,
            )
            return OrchestratorResponse(
                response_text=confirmation_message,
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

    @staticmethod
    def _normalize_phrase(text: str) -> str:
        cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
        return re.sub(r"\s+", " ", cleaned).strip()
