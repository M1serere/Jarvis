from __future__ import annotations

from typing import Any

from tools.base import BaseTool
from tools.implementations.browser_search import BrowserSearchTool
from tools.implementations.create_file import CreateFileTool
from tools.implementations.open_file import OpenFileTool
from tools.implementations.open_url import OpenUrlTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        self.register(OpenUrlTool())
        self.register(BrowserSearchTool())
        self.register(CreateFileTool())
        self.register(OpenFileTool())

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tools

    def execute(self, tool_name: str, args: dict[str, Any]) -> str:
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ValueError(f"Tool '{tool_name}' is not registered.")
        return tool.run(args)

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self._tools.values()
        ]