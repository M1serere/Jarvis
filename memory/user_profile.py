from __future__ import annotations

from core.config import DEFAULT_USER_NAME
from memory.persistent_memory import PersistentMemory


class UserProfile:
    _PLACEHOLDER_NAMES = {
        DEFAULT_USER_NAME,
        "Р“РѕСЃРїРѕР¶Р°",
    }

    def __init__(self, storage: PersistentMemory) -> None:
        self.storage = storage

    def set_name(self, name: str) -> None:
        clean_name = name.strip()
        if clean_name:
            self.storage.set("user_name", clean_name)

    def _is_placeholder_name(self, name: str) -> bool:
        return name.strip() in self._PLACEHOLDER_NAMES

    def has_name(self) -> bool:
        stored_name = self.storage.get("user_name", "")
        if not isinstance(stored_name, str):
            return False

        clean_name = stored_name.strip()
        return bool(clean_name and not self._is_placeholder_name(clean_name))

    def get_saved_name(self) -> str | None:
        stored_name = self.storage.get("user_name", "")
        if not isinstance(stored_name, str):
            return None

        clean_name = stored_name.strip()
        if not clean_name or self._is_placeholder_name(clean_name):
            return None
        return clean_name

    def get_name(self) -> str:
        return self.get_saved_name() or DEFAULT_USER_NAME
