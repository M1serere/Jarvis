from core.orchestrator import JarvisOrchestrator


def main() -> None:
    orchestrator = JarvisOrchestrator()

    print("Jarvis core started. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Jarvis: Goodbye.")
            break

        response = orchestrator.handle_user_input(user_input)
        print(f"Jarvis: {response.response_text}")


if __name__ == "__main__":
    main()