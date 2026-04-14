from __future__ import annotations

import urllib.parse
import webbrowser
from typing import Any

from tools.base import BaseTool


class BrowserSearchTool(BaseTool):
    name = "browser_search"
    description = "Открывает поиск Google по переданному запросу."

    def run(self, args: dict[str, Any]) -> str:
        query = str(args.get("query", "")).strip()

        if not query:
            return "Не удалось выполнить поиск: пустой запрос."

        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}"

        opened = webbrowser.open(url)
        if opened:
            return f"Ищу в Google: {query}"

        return f"Не удалось открыть поиск Google для запроса: {query}"