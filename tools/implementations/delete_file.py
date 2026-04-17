from __future__ import annotations

from pathlib import Path
from typing import Any

from core.config import WORKSPACE_DIR
from tools.base import BaseTool


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Удаляет файл из рабочей папки ассистента."
    risk_level = "dangerous"

    def run(self, args: dict[str, Any]) -> str:
        filename = str(args.get("filename", "")).strip()

        if not filename:
            return "Не удалось удалить файл: имя файла не указано."

        safe_filename = Path(filename).name
        file_path = WORKSPACE_DIR / safe_filename

        if not file_path.exists():
            return f"Файл не найден: {safe_filename}"

        if not file_path.is_file():
            return f"Это не файл: {safe_filename}"

        file_path.unlink()
        return f"Файл удалён: {safe_filename}"