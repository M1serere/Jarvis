from voice.voice_controller import VoiceController
from voice.wake_word import WakeWordListener


def main() -> None:
    voice_controller = VoiceController()
    wake_listener = WakeWordListener(keyword="jarvis")

    print("Jarvis voice mode is running.")
    print("Say 'Jarvis' to activate the assistant.")
    print("Press Ctrl+C to stop.\n")

    try:
        wake_listener.listen(voice_controller.handle_wake)
    except KeyboardInterrupt:
        print("\nJarvis stopped.")


if __name__ == "__main__":
    main()
