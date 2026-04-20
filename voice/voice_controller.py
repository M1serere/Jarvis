from __future__ import annotations

import random
import re
import threading

from core import autostart
from core.config import WORK_TIMER_SECONDS
from core.orchestrator import JarvisOrchestrator
from core.settings import AppSettings, SettingsStore
from core.work_timer import WorkTimer
from ui.status_window import StatusWindow
from voice.stt import SpeechToText
from voice.tts import TextToSpeech


class VoiceController:
    SLEEP_COMMANDS = {
        "отдохни",
        "можешь отдохнуть",
        "джарвис отдохни",
        "джарвис можешь отдохнуть",
    }

    def __init__(self) -> None:
        self.settings_store = SettingsStore()
        self.settings = self.settings_store.load()
        self.stt = SpeechToText()
        self.tts = TextToSpeech(volume=self.settings.voice_volume)
        self.ui = StatusWindow(
            voice_volume=self.settings.voice_volume,
            on_voice_volume_change=self.set_voice_volume,
            autostart_enabled=self.settings.autostart_enabled,
            on_autostart_change=self.set_autostart,
            overlay_mode=self.settings.overlay_mode,
            on_overlay_mode_change=self.set_overlay_mode,
        )
        self.work_timer = WorkTimer(
            notify_callback=self.notify_break,
            work_limit_seconds=WORK_TIMER_SECONDS,
        )
        self.orchestrator = JarvisOrchestrator(
            status_ui=self.ui,
            work_time_provider=self.work_timer.get_elapsed_seconds,
        )
        self._activation_lock = threading.Lock()
        self._is_awake = False
        self._sync_autostart()

    def set_voice_volume(self, volume: int) -> None:
        safe_volume = max(0, min(int(volume), 100))
        self.settings = AppSettings(
            voice_volume=safe_volume,
            autostart_enabled=self.settings.autostart_enabled,
            overlay_mode=self.settings.overlay_mode,
        )
        self.tts.set_volume(safe_volume)
        try:
            self.settings_store.save(self.settings)
        except Exception:
            pass

    def set_autostart(self, enabled: bool) -> None:
        desired_state = bool(enabled)
        success = autostart.set_enabled(desired_state) if autostart.is_supported() else False

        self.settings = AppSettings(
            voice_volume=self.settings.voice_volume,
            autostart_enabled=desired_state if success else autostart.is_enabled(),
            overlay_mode=self.settings.overlay_mode,
        )
        self.ui.set_autostart_value(self.settings.autostart_enabled)

        try:
            self.settings_store.save(self.settings)
        except Exception:
            pass

    def _sync_autostart(self) -> None:
        if autostart.is_supported():
            actual_state = autostart.set_enabled(self.settings.autostart_enabled)
            self.settings = AppSettings(
                voice_volume=self.settings.voice_volume,
                autostart_enabled=actual_state and self.settings.autostart_enabled,
                overlay_mode=self.settings.overlay_mode,
            )
        else:
            self.settings = AppSettings(
                voice_volume=self.settings.voice_volume,
                autostart_enabled=False,
                overlay_mode=self.settings.overlay_mode,
            )

        self.ui.set_autostart_value(self.settings.autostart_enabled)

        try:
            self.settings_store.save(self.settings)
        except Exception:
            pass

    def set_overlay_mode(self, enabled: bool) -> None:
        self.settings = AppSettings(
            voice_volume=self.settings.voice_volume,
            autostart_enabled=self.settings.autostart_enabled,
            overlay_mode=bool(enabled),
        )
        try:
            self.settings_store.save(self.settings)
        except Exception:
            pass

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
        self._set_idle_status()

    def _set_idle_status(self) -> None:
        detail = "Ожидание команды" if self._is_awake else "Ожидание wake word"
        self.ui.set_status("Готов", detail)

    @staticmethod
    def _normalize_command(text: str) -> str:
        normalized = re.sub(r"[^\w\s-]", " ", text.lower())
        return " ".join(normalized.split())

    def _is_sleep_command(self, text: str) -> bool:
        return self._normalize_command(text) in self.SLEEP_COMMANDS

    def run_once(self) -> bool:
        self.ui.set_status("Слушает", "Жду голосовую команду")
        user_text = self.stt.listen(timeout=None, phrase_time_limit=None)
        
        if user_text and self.ui:
            self.ui.add_user_command(user_text)

        if not user_text:
            self.ui.set_status("Готов", "Не удалось распознать речь")
            self.tts.speak("Я не расслышал, повтори.")
            self._set_idle_status()
            return True

        if user_text.startswith("Ошибка STT:"):
            self.ui.set_status("Готов", "Ошибка распознавания речи")
            self.tts.speak("Возникла ошибка распознавания речи.")
            self._set_idle_status()
            return True

        if self._is_sleep_command(user_text):
            self._is_awake = False
            self.ui.set_status("Готов", "Переход в режим ожидания")
            self.tts.speak("Хорошо. Буду ждать обращения по ключевому слову.")
            self._set_idle_status()
            return False

        response = self.orchestrator.handle_user_input(user_text)
        self.ui.set_status("Говорит", "Озвучиваю ответ")
        self.tts.speak(response.response_text)
        if not response.keep_awake:
            self._is_awake = False
            self.ui.set_status("Готов", "Ожидание wake word")
            return False
        self._set_idle_status()
        return True

    def handle_wake(self) -> None:
        if not self._activation_lock.acquire(blocking=False):
            return

        try:
            if self._is_awake:
                self._set_idle_status()
                return

            self._is_awake = True
            self.ui.set_status("Активирован", "Wake word detected")
            self.tts.speak("Чем могу помочь, госпожа?")

            while self._is_awake:
                if not self.run_once():
                    break
        finally:
            self._set_idle_status()
            self._activation_lock.release()
