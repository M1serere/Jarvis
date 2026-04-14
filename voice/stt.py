from __future__ import annotations

import speech_recognition as sr


class SpeechToText:
    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()

    def listen(self) -> str:
        with sr.Microphone() as source:
            print("🎤 Слушаю...")
            audio = self.recognizer.listen(source)

        try:
            text = self.recognizer.recognize_google(audio, language="ru-RU")
            print(f"🧠 Распознано: {text}")
            return text
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            return f"Ошибка STT: {e}"