# from __future__ import annotations

# from core.orchestrator import JarvisOrchestrator
# from voice.stt import SpeechToText
# from voice.tts import TextToSpeech


# class VoiceController:
#     def __init__(self) -> None:
#         self.stt = SpeechToText()
#         self.tts = TextToSpeech()
#         self.orchestrator = JarvisOrchestrator()

#     def run_once(self) -> None:
#         user_text = self.stt.listen()

#         if not user_text:
#             self.tts.speak("Я не расслышал, повтори.")
#             return

#         response = self.orchestrator.handle_user_input(user_text)
#         self.tts.speak(response.response_text)

from __future__ import annotations

from core.orchestrator import JarvisOrchestrator
from ui.status_window import StatusWindow
from voice.stt import SpeechToText
from voice.tts import TextToSpeech


class VoiceController:
    def __init__(self) -> None:
        self.ui = StatusWindow()
        self.ui.start_in_thread()

        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.orchestrator = JarvisOrchestrator(status_ui=self.ui)

    def run_once(self) -> None:
        self.ui.set_status("Слушает", "Жду голосовую команду")
        user_text = self.stt.listen()

        if not user_text:
            self.ui.set_status("Готов", "Не удалось распознать речь")
            self.tts.speak("Я не расслышал, повтори.")
            return

        response = self.orchestrator.handle_user_input(user_text)
        self.ui.set_status("Говорит", "Озвучиваю ответ")
        self.tts.speak(response.response_text)
        self.ui.set_status("Готов", "Ожидание команды")