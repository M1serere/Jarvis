import threading

from voice.voice_controller import VoiceController
from voice.wake_word import WakeWordListener


def main() -> None:
    voice_controller = VoiceController()
    wake_listener = WakeWordListener(keywords=["джарвис", "jarvis"])

    print("Jarvis voice mode is running.")
    print("Say 'Jarvis' to activate the assistant.")
    print("Press Ctrl+C to stop.\n")

    listener_thread = threading.Thread(
        target=wake_listener.listen,
        args=(voice_controller.handle_wake,),
        daemon=True,
    )
    listener_thread.start()
    voice_controller.start_work_timer()

    try:
        voice_controller.ui.run()
    except KeyboardInterrupt:
        print("\nJarvis stopped.")



if __name__ == "__main__":
    main()
