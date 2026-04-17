from __future__ import annotations

from tools.registry import ToolRegistry


class PermissionPolicy:
    def __init__(self, tool_registry: ToolRegistry) -> None:
        self.tool_registry = tool_registry

    def get_risk_level(self, tool_name: str | None) -> str:
        if not tool_name:
            return "safe"

        tool = self.tool_registry.get_tool(tool_name)
        if tool is None:
            return "dangerous"

        return tool.risk_level