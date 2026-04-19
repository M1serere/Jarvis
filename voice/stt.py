from __future__ import annotations

import speech_recognition as sr


class SpeechToText:
    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()

    def listen(self) -> str:
        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = self.recognizer.listen(source)
        except OSError as exc:
            return f"Ошибка STT: {exc}"

        try:
            text = self.recognizer.recognize_google(audio, language="ru-RU")
            print(f"Распознано: {text}")
            return text
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as exc:
            return f"Ошибка STT: {exc}"
