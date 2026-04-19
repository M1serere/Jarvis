from __future__ import annotations

from contextlib import suppress

import speech_recognition as sr


class SpeechToText:
    def __init__(
        self,
        language: str = "ru-RU",
        pause_threshold: float = 1.0,
        non_speaking_duration: float = 0.5,
        phrase_threshold: float = 0.3,
    ) -> None:
        self.recognizer = sr.Recognizer()
        self.language = language
        # Finish capture after roughly one second of silence to avoid clipping.
        self.recognizer.pause_threshold = pause_threshold
        self.recognizer.non_speaking_duration = non_speaking_duration
        self.recognizer.phrase_threshold = phrase_threshold

    @staticmethod
    def _close_microphone(source: sr.Microphone) -> None:
        with suppress(OSError, AttributeError):
            source.__exit__(None, None, None)

    def listen(self, timeout: float | None = None, phrase_time_limit: float | None = None) -> str:
        source = sr.Microphone()
        try:
            entered_source = source.__enter__()
            print("Listening...")
            audio = self.recognizer.listen(
                entered_source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit,
            )
        except OSError as exc:
            return f"Ошибка STT: {exc}"
        except sr.WaitTimeoutError:
            return ""
        finally:
            self._close_microphone(source)

        try:
            text = self.recognizer.recognize_google(audio, language=self.language)
            print(f"Распознано: {text}")
            return text
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as exc:
            return f"Ошибка STT: {exc}"
