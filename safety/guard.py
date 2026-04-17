# from __future__ import annotations

# from core.models import AssistantDecision
# from tools.registry import ToolRegistry


# class SafetyGuard:
#     def __init__(self, tool_registry: ToolRegistry | None = None) -> None:
#         self.tool_registry = tool_registry

#     def approve(self, decision: AssistantDecision) -> bool:
#         if decision.requires_confirmation:
#             return False

#         if (
#             decision.decision_type == "tool_call"
#             and decision.tool_name
#             and self.tool_registry is not None
#         ):
#             tool = self.tool_registry.get_tool(decision.tool_name)
#             if tool and tool.risk_level == "dangerous":
#                 return False

#         return True

#     def get_block_message(self, decision: AssistantDecision) -> str:
#         if decision.requires_confirmation and decision.tool_name:
#             return (
#                 f"Подтвердить действие '{decision.tool_name}' "
#                 f"с аргументами {decision.tool_args}? "
#                 f"Ответь 'да' или 'нет'."
#             )

#         if (
#             decision.decision_type == "tool_call"
#             and decision.tool_name
#             and self.tool_registry is not None
#         ):
#             tool = self.tool_registry.get_tool(decision.tool_name)
#             if tool and tool.risk_level == "dangerous":
#                 return f"Действие '{decision.tool_name}' заблокировано как опасное."

#         return "Действие не прошло проверку безопасности."

from __future__ import annotations

from core.models import AssistantDecision
from safety.messages import build_confirmation_message
from safety.policy import PermissionPolicy
from tools.registry import ToolRegistry


class SafetyGuard:
    def __init__(self, tool_registry: ToolRegistry | None = None) -> None:
        self.tool_registry = tool_registry
        self.policy = PermissionPolicy(tool_registry) if tool_registry else None

    def approve(self, decision: AssistantDecision) -> bool:
        if decision.decision_type != "tool_call":
            return True

        if decision.requires_confirmation:
            return False

        if decision.tool_name and self.policy is not None:
            risk_level = self.policy.get_risk_level(decision.tool_name)
            if risk_level in {"confirm", "dangerous"}:
                return False

        return True

    def get_block_message(self, decision: AssistantDecision) -> str:
        if decision.decision_type == "tool_call":
            return build_confirmation_message(
                tool_name=decision.tool_name,
                tool_args=decision.tool_args,
            )

        return "Действие не прошло проверку безопасности."