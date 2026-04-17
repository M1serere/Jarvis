from __future__ import annotations

from typing import Any

from tools.base import BaseTool
from tools.implementations.browser_search import BrowserSearchTool
from tools.implementations.create_file import CreateFileTool
from tools.implementations.edit_file import EditFileTool
from tools.implementations.get_programming_news import GetProgrammingNewsTool
from tools.implementations.get_weather import GetWeatherTool
from tools.implementations.open_file import OpenFileTool
from tools.implementations.open_url import OpenUrlTool

from tools.implementations.music_control import MusicControlTool

from tools.implementations.delete_file import DeleteFileTool

class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        self.register(OpenUrlTool())
        self.register(BrowserSearchTool())
        self.register(CreateFileTool())
        self.register(OpenFileTool())
        self.register(EditFileTool())
        self.register(GetWeatherTool())
        self.register(GetProgrammingNewsTool())
        self.register(MusicControlTool())
        self.register(DeleteFileTool())

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tools

    def get_tool(self, tool_name: str) -> BaseTool | None:
        return self._tools.get(tool_name)

    def execute(self, tool_name: str, args: dict[str, Any]) -> str:
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ValueError(f"Tool '{tool_name}' is not registered.")
        return tool.run(args)

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "risk_level": tool.risk_level,
            }
            for tool in self._tools.values()
        ]