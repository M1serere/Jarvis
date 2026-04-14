from __future__ import annotations

from pathlib import Path
from typing import Any

from core.config import WORKSPACE_DIR
from tools.base import BaseTool


class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Создаёт текстовый файл в рабочей папке ассистента."

    def run(self, args: dict[str, Any]) -> str:
        filename = str(args.get("filename", "")).strip()
        content = str(args.get("content", ""))

        if not filename:
            return "Не удалось создать файл: имя файла не указано."

        safe_filename = Path(filename).name
        file_path = WORKSPACE_DIR / safe_filename

        if file_path.exists():
            return f"Файл уже существует: {safe_filename}"

        file_path.write_text(content, encoding="utf-8")
        return f"Файл создан: {safe_filename}"