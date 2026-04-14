from __future__ import annotations


class ToolRegistry:
    def has_tool(self, tool_name: str) -> bool:
        return False

    def execute(self, tool_name: str, args: dict) -> str:
        raise NotImplementedError("Tools are not implemented yet.")