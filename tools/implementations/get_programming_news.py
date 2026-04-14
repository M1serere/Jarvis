from __future__ import annotations

from typing import Any

from core.config import HTTP_TIMEOUT_SECONDS, PROGRAMMING_NEWS_FEEDS
from services.http_client import HttpClient
from services.news_service import NewsService
from tools.base import BaseTool


class GetProgrammingNewsTool(BaseTool):
    name = "get_programming_news"
    description = "Получает свежие новости программирования."
    risk_level = "safe"

    def __init__(self) -> None:
        http_client = HttpClient(timeout=HTTP_TIMEOUT_SECONDS)
        self.news_service = NewsService(http_client=http_client)

    def run(self, args: dict[str, Any]) -> str:
        limit = int(args.get("limit", 5))

        try:
            headlines = self.news_service.get_top_headlines(
                feed_urls=PROGRAMMING_NEWS_FEEDS,
                limit=limit,
            )

            if not headlines:
                return "Не удалось получить новости программирования."

            formatted = "\n".join(
                f"{index + 1}. {headline}"
                for index, headline in enumerate(headlines)
            )
            return f"Свежие новости программирования:\n{formatted}"
        except Exception as exc:
            return f"Не удалось получить новости программирования: {exc}"