from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PersistentMemory:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if not self.file_path.exists():
            self.data = {}
            return

        try:
            self.data = json.loads(self.file_path.read_text(encoding="utf-8"))
        except Exception:
            self.data = {}

    def _save(self) -> None:
        self.file_path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self._save()
