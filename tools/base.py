from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal

ToolRiskLevel = Literal["safe", "confirm", "dangerous"]


class BaseTool(ABC):
    name: str
    description: str
    risk_level: ToolRiskLevel = "safe"

    @abstractmethod
    def run(self, args: dict[str, Any]) -> str:
        raise NotImplementedError