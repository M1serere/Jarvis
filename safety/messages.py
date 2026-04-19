from __future__ import annotations


def build_confirmation_message(tool_name: str | None, tool_args: dict) -> str:
    if tool_name == "delete_file":
        filename = tool_args.get("filename", "неизвестный файл")
        return f"Ты уверен, что хочешь удалить файл {filename}? Ответь 'да' или 'нет'."

    if tool_name == "create_file":
        filename = tool_args.get("filename", "неизвестный файл")
        return f"Подтвердить создание файла {filename}? Ответь 'да' или 'нет'."

    if tool_name == "edit_file":
        filename = tool_args.get("filename", "неизвестный файл")
        mode = tool_args.get("mode", "")
        if mode == "replace_all":
            return (
                f"Подтвердить полную замену содержимого файла {filename}? "
                f"Ответь 'да' или 'нет'."
            )
        if mode == "append":
            return f"Подтвердить добавление текста в файл {filename}? Ответь 'да' или 'нет'."
        if mode == "replace_text":
            return f"Подтвердить замену текста в файле {filename}? Ответь 'да' или 'нет'."

        return f"Подтвердить изменение файла {filename}? Ответь 'да' или 'нет'."

    if tool_name == "system_power":
        action = str(tool_args.get("action", "")).strip().lower()
        if action == "sleep":
            return "Подтвердить перевод компьютера в спящий режим? Ответь 'да' или 'нет'."
        if action == "shutdown":
            return "Подтвердить выключение компьютера? Ответь 'да' или 'нет'."
        return "Подтвердить действие с питанием компьютера? Ответь 'да' или 'нет'."

    if tool_name:
        return f"Подтвердить действие '{tool_name}'? Ответь 'да' или 'нет'."

    return "Подтвердить действие? Ответь 'да' или 'нет'."
