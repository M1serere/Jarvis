from core.orchestrator import JarvisOrchestrator
from voice.voice_controller import VoiceController


def run_cli() -> None:
    orchestrator = JarvisOrchestrator()

    print("Jarvis CLI mode. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            break

        response = orchestrator.handle_user_input(user_input)
        print(f"Jarvis: {response.response_text}")


def run_voice() -> None:
    vc = VoiceController()

    print("Jarvis voice mode. Press Enter to speak. Type 'exit' to quit.\n")

    while True:
        cmd = input("Press Enter to talk...")

        if cmd.strip().lower() == "exit":
            break

        vc.run_once()


def main() -> None:
    mode = input("Select mode (cli / voice): ").strip().lower()

    if mode == "voice":
        run_voice()
    else:
        run_cli()


if __name__ == "__main__":
    main()