from __future__ import annotations

import pyttsx3


class TextToSpeech:
    def __init__(self) -> None:
        self.engine = pyttsx3.init()
        self._configure_voice()

    def _configure_voice(self) -> None:
        voices = self.engine.getProperty("voices")

        for voice in voices:
            if "male" in voice.name.lower() or "david" in voice.name.lower():
                self.engine.setProperty("voice", voice.id)
                break

        self.engine.setProperty("rate", 180)

    def speak(self, text: str) -> None:
        print(f"🔊 Jarvis: {text}")
        self.engine.say(text)
        self.engine.runAndWait()