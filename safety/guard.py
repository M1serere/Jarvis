from __future__ import annotations

from core.models import AssistantDecision
from tools.registry import ToolRegistry


class SafetyGuard:
    def __init__(self, tool_registry: ToolRegistry | None = None) -> None:
        self.tool_registry = tool_registry

    def approve(self, decision: AssistantDecision) -> bool:
        if decision.requires_confirmation:
            return False

        if (
            decision.decision_type == "tool_call"
            and decision.tool_name
            and self.tool_registry is not None
        ):
            tool = self.tool_registry.get_tool(decision.tool_name)
            if tool and tool.risk_level == "dangerous":
                return False

        return True

    def get_block_message(self, decision: AssistantDecision) -> str:
        if decision.requires_confirmation and decision.tool_name:
            return (
                f"Подтвердить действие '{decision.tool_name}' "
                f"с аргументами {decision.tool_args}? "
                f"Ответь 'да' или 'нет'."
            )

        if (
            decision.decision_type == "tool_call"
            and decision.tool_name
            and self.tool_registry is not None
        ):
            tool = self.tool_registry.get_tool(decision.tool_name)
            if tool and tool.risk_level == "dangerous":
                return f"Действие '{decision.tool_name}' заблокировано как опасное."

        return "Действие не прошло проверку безопасности."