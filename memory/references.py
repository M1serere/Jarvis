from __future__ import annotations

from typing import Any


class ReferenceResolver:
    def __init__(self) -> None:
        self.last_file: str | None = None

    def remember_file(self, filename: str) -> None:
        self.last_file = filename

    def resolve(self, args: dict[str, Any]) -> dict[str, Any]:
        if "filename" in args:
            if args["filename"] in {"его", "её", "этот", "тот"}:
                if self.last_file:
                    args["filename"] = self.last_file
        return args