from __future__ import annotations

import webbrowser
from typing import Any
from urllib.parse import urlparse

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
            return self._build_success_message(url)

        return f"Не удалось открыть сайт: {url}"

    @staticmethod
    def _normalize_url(url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        return f"https://{url}"

    @staticmethod
    def _build_success_message(url: str) -> str:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()

        if any(domain in host for domain in ("youtube.com", "youtu.be")):
            return "Открываю. Приятного прослушивания."

        if OpenUrlTool._looks_like_news_article(host, path):
            return "Открываю новость. Приятного чтения."

        return "Открываю сайт."

    @staticmethod
    def _looks_like_news_article(host: str, path: str) -> bool:
        if "habr.com" in host and path.startswith("/"):
            return path not in {"", "/"} and "/news" not in path

        news_hosts = (
            "lenta.ru",
            "ria.ru",
            "tass.ru",
            "meduza.io",
            "bbc.com",
            "cnn.com",
            "theverge.com",
        )
        if any(domain in host for domain in news_hosts):
            return path not in {"", "/"}

        news_markers = ("/news/", "/article/", "/articles/", "/story/", "/stories/")
        return any(marker in path for marker in news_markers)
