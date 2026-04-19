from __future__ import annotations

from collections.abc import Callable

import speech_recognition as sr


class WakeWordListener:
    def __init__(
        self,
        keywords: list[str] | None = None,
        language: str = "ru-RU",
        timeout: float = 1.5,
        phrase_time_limit: float = 2.5,
    ) -> None:
        self.keywords = [k.lower() for k in (keywords or ["джарвис", "jarvis"])]
        self.language = language
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit
        self.recognizer = sr.Recognizer()

    def listen(self, callback: Callable[[], None]) -> None:
        print(f"Listening for wake words: {', '.join(self.keywords)}")

        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

            while True:
                try:
                    audio = self.recognizer.listen(
                        source,
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
                    print(f"Wake recognized: {text}")
                except (sr.UnknownValueError, sr.RequestError):
                    continue

                if any(keyword in text for keyword in self.keywords):
                    print("Wake word detected!")
                    callback()