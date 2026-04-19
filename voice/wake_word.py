from __future__ import annotations

import speech_recognition as sr


class WakeWordListener:
    def __init__(
        self,
        keyword: str = "jarvis",
        language: str = "en-US",
        timeout: float = 1.5,
        phrase_time_limit: float = 2.5,
    ) -> None:
        self.keyword = keyword.lower()
        self.language = language
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit
        self.recognizer = sr.Recognizer()

    def listen(self, callback) -> None:
        print("Listening for wake word 'Jarvis'...")

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
                except (sr.UnknownValueError, sr.RequestError):
                    continue

                if self.keyword in text:
                    print("Wake word detected!")
                    callback()
