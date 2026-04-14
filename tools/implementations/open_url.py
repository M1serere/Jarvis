from __future__ import annotations

import webbrowser
from typing import Any

from tools.base import BaseTool


class OpenUrlTool(BaseTool):
    name = "open_url"
    description = "Открывает указанный URL в браузере по умолчанию."

    def run(self, args: dict[str, Any]) -> str:
        raw_url = str(args.get("url", "")).strip()

        if not raw_url:
            return "Не удалось открыть сайт: не передан адрес."

        url = self._normalize_url(raw_url)
        opened = webbrowser.open(url)

        if opened:
            return f"Открываю сайт: {url}"

        return f"Не удалось открыть сайт: {url}"

    @staticmethod
    def _normalize_url(url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        return f"https://{url}"