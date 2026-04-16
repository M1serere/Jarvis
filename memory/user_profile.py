from __future__ import annotations

from memory.persistent_memory import PersistentMemory


class UserProfile:
    def __init__(self, storage: PersistentMemory) -> None:
        self.storage = storage

    def set_name(self, name: str) -> None:
        self.storage.set("user_name", name)

    def get_name(self) -> str | None:
        return self.storage.get("user_name")