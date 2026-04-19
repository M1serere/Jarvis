from __future__ import annotations

import threading

from core.orchestrator import JarvisOrchestrator
from ui.status_window import StatusWindow
from voice.stt import SpeechToText
from voice.tts import TextToSpeech


class VoiceController:
    def __init__(self) -> None:
        self.ui = StatusWindow()
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.orchestrator = JarvisOrchestrator(status_ui=self.ui)
        self._activation_lock = threading.Lock()

    def run_once(self) -> None:
        self.ui.set_status("Слушает", "Жду голосовую команду")
        user_text = self.stt.listen()

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
