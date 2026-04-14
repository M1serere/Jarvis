from __future__ import annotations

from pathlib import Path
from typing import Any

from core.config import WORKSPACE_DIR
from tools.base import BaseTool


class OpenFileTool(BaseTool):
    name = "open_file"
    description = "Открывает текстовый файл из рабочей папки и читает его содержимое."
    risk_level = "safe"

    def run(self, args: dict[str, Any]) -> str:
        filename = str(args.get("filename", "")).strip()

        if not filename:
            return "Не удалось открыть файл: имя файла не указано."

        safe_filename = Path(filename).name
        file_path = WORKSPACE_DIR / safe_filename

        if not file_path.exists():
            return f"Файл не найден: {safe_filename}"

        if not file_path.is_file():
            return f"Это не файл: {safe_filename}"

        content = file_path.read_text(encoding="utf-8")
        if not content:
            return f"Файл пуст: {safe_filename}"

        max_preview_length = 1500
        preview = content[:max_preview_length]

        if len(content) > max_preview_length:
            return (
                f"Содержимое файла {safe_filename} "
                f"(показаны первые {max_preview_length} символов из {len(content)}):\n"
                f"{preview}"
            )

        return f"Содержимое файла {safe_filename}:\n{preview}"