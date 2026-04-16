from __future__ import annotations

from memory.persistent_memory import PersistentMemory


class FactsMemory:
    def __init__(self, storage: PersistentMemory) -> None:
        self.storage = storage

    def add_fact(self, fact: str) -> None:
        fact = fact.strip()
        if not fact:
            return

        facts = self.storage.get("facts", [])
        if fact not in facts:
            facts.append(fact)
            self.storage.set("facts", facts)

    def get_facts(self) -> list[str]:
        return self.storage.get("facts", [])