from __future__ import annotations

from pathlib import Path
from typing import Any

from core.config import WORKSPACE_DIR
from tools.base import BaseTool


class OpenFileTool(BaseTool):
    name = "open_file"
    description = "Открывает текстовый файл из рабочей папки и читает его содержимое."

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
        content_preview = content[:1000]

        if not content_preview:
            return f"Файл пуст: {safe_filename}"

        return f"Содержимое файла {safe_filename}:\n{content_preview}"