from __future__ import annotations

from pathlib import Path
from typing import Any

from core.config import WORKSPACE_DIR
from tools.base import BaseTool


class EditFileTool(BaseTool):
    name = "edit_file"
    description = "Изменяет текстовый файл в рабочей папке ассистента."
    risk_level = "confirm"

    def run(self, args: dict[str, Any]) -> str:
        filename = str(args.get("filename", "")).strip()
        mode = str(args.get("mode", "")).strip()
        content = str(args.get("content", ""))
        old_text = str(args.get("old_text", ""))
        new_text = str(args.get("new_text", ""))

        if not filename:
            return "Не удалось изменить файл: имя файла не указано."

        safe_filename = Path(filename).name
        file_path = WORKSPACE_DIR / safe_filename

        if not file_path.exists():
            return f"Файл не найден: {safe_filename}"

        if not file_path.is_file():
            return f"Это не файл: {safe_filename}"

        current_text = file_path.read_text(encoding="utf-8")

        if mode == "replace_all":
            file_path.write_text(content, encoding="utf-8")
            return f"Файл полностью обновлён: {safe_filename}"

        if mode == "append":
            updated_text = current_text + content
            file_path.write_text(updated_text, encoding="utf-8")
            return f"Текст добавлен в файл: {safe_filename}"

        if mode == "replace_text":
            if not old_text:
                return "Не удалось заменить текст: не указан old_text."

            if old_text not in current_text:
                return f"Текст для замены не найден в файле: {safe_filename}"

            updated_text = current_text.replace(old_text, new_text)
            file_path.write_text(updated_text, encoding="utf-8")
            return f"Текст в файле заменён: {safe_filename}"

        return (
            "Не удалось изменить файл: неизвестный режим. "
            "Поддерживаются replace_all, append, replace_text."
        )