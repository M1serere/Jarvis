from __future__ import annotations

import random
import threading

from core.config import WORK_TIMER_SECONDS
from core.orchestrator import JarvisOrchestrator
from core.work_timer import WorkTimer
from ui.status_window import StatusWindow
from voice.stt import SpeechToText
from voice.tts import TextToSpeech


class VoiceController:
    def __init__(self) -> None:
        self.ui = StatusWindow()
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.work_timer = WorkTimer(
            notify_callback=self.notify_break,
            work_limit_seconds=WORK_TIMER_SECONDS,
        )
        self.orchestrator = JarvisOrchestrator(
            status_ui=self.ui,
            work_time_provider=self.work_timer.get_elapsed_seconds,
        )
        self._activation_lock = threading.Lock()

    def start_work_timer(self) -> None:
        self.work_timer.start()

    def notify_break(self) -> None:
        reminder_options = [
            "Госпожа, вы работаете больше трёх часов. Не хотите ли сделать перерыв?",
            "Госпожа, вы уже работаете больше трёх часов. Возможно, пора немного отдохнуть.",
            "Госпожа, прошло уже более трёх часов работы. Может быть, стоит сделать небольшой перерыв?",
        ]
        reminder = random.choice(reminder_options)
        print("[TIMER] Пора сделать перерыв")
        self.ui.set_status("Напоминание", "Пора сделать перерыв")
        self.tts.speak(reminder)
        self.ui.set_status("Готов", "Ожидание wake word")

    def run_once(self) -> None:
        self.ui.set_status("Слушает", "Жду голосовую команду")
        user_text = self.stt.listen()
        
        if user_text and self.ui:
            self.ui.add_user_command(user_text)

        if not user_text or user_text.startswith("Ошибка STT:"):
            self.ui.set_status("Готов", "Не удалось распознать речь")
            self.tts.speak("Я не расслышал, повтори.")
            return

        response = self.orchestrator.handle_user_input(user_text)
        self.ui.set_status("Говорит", "Озвучиваю ответ")
        self.tts.speak(response.response_text)
        self.ui.set_status("Готов", "Ожидание команды")

    def handle_wake(self) -> None:
        if not self._activation_lock.acquire(blocking=False):
            return

        try:
            self.ui.set_status("Активирован", "Wake word detected")
            self.tts.speak("Чем могу помочь, госпожа?")
            self.run_once()
        finally:
            self.ui.set_status("Готов", "Ожидание wake word")
            self._activation_lock.release()
