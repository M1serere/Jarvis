from __future__ import annotations

from core.orchestrator import JarvisOrchestrator
from voice.stt import SpeechToText
from voice.tts import TextToSpeech


class VoiceController:
    def __init__(self) -> None:
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.orchestrator = JarvisOrchestrator()

    def run_once(self) -> None:
        user_text = self.stt.listen()

        if not user_text:
            self.tts.speak("Я не расслышал, повтори.")
            return

        response = self.orchestrator.handle_user_input(user_text)
        self.tts.speak(response.response_text)