from __future__ import annotations

from core.config import DEFAULT_USER_NAME
from memory.persistent_memory import PersistentMemory


class UserProfile:
    def __init__(self, storage: PersistentMemory) -> None:
        self.storage = storage

    def set_name(self, name: str) -> None:
        clean_name = name.strip()
        if clean_name:
            self.storage.set("user_name", clean_name)

    def get_name(self) -> str:
        return self.storage.get("user_name", DEFAULT_USER_NAME)