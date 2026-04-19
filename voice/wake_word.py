from __future__ import annotations

from contextlib import suppress
from collections.abc import Callable
import re

import speech_recognition as sr


class WakeWordListener:
    def __init__(
        self,
        keywords: list[str] | None = None,
        language: str = "ru-RU",
        timeout: float = 1.5,
        phrase_time_limit: float = 2.5,
        debug: bool = False,
    ) -> None:
        self.keywords = [
            self._normalize_text(k)
            for k in (keywords or ["\u0434\u0436\u0430\u0440\u0432\u0438\u0441", "jarvis"])
        ]
        self.language = language
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit
        self.debug = debug
        self.recognizer = sr.Recognizer()

    @staticmethod
    def _close_microphone(source: sr.Microphone) -> None:
        with suppress(OSError, AttributeError):
            source.__exit__(None, None, None)

    def listen(self, callback: Callable[[], None]) -> None:
        print(f"Listening for wake words: {', '.join(self.keywords)}")

        while True:
            should_activate = False
            source = sr.Microphone()

            try:
                entered_source = source.__enter__()
                self.recognizer.adjust_for_ambient_noise(entered_source, duration=1)

                while True:
                    try:
                        audio = self.recognizer.listen(
                            entered_source,
                            timeout=self.timeout,
                            phrase_time_limit=self.phrase_time_limit,
                        )
                    except sr.WaitTimeoutError:
                        continue

                    try:
                        text = self.recognizer.recognize_google(
                            audio,
                            language=self.language,
                        ).lower()
                        if self.debug:
                            print(f"Wake recognized: {text}")
                    except (sr.UnknownValueError, sr.RequestError):
                        continue

                    if self._is_wake_phrase(text):
                        print("Wake word detected!")
                        should_activate = True
                        break
            except OSError as exc:
                if self.debug:
                    print(f"Wake microphone error: {exc}")
                continue
            finally:
                self._close_microphone(source)

            if should_activate:
                callback()

    @staticmethod
    def _normalize_text(text: str) -> str:
        normalized = re.sub(r"[^\w\s-]", " ", text.lower())
        return " ".join(normalized.split())

    def _is_wake_phrase(self, text: str) -> bool:
        normalized_text = self._normalize_text(text)
        if not normalized_text:
            return False

        allowed_prefixes = ("", "\u044d\u0439", "hey", "ok", "okay")

        for keyword in self.keywords:
            for prefix in allowed_prefixes:
                allowed_phrase = f"{prefix} {keyword}".strip()
                if normalized_text == allowed_phrase:
                    return True

        return False
