from __future__ import annotations

import html
import re
from dataclasses import dataclass

from services.http_client import HttpClient


HABR_DAILY_NEWS_URL = "https://habr.com/ru/news/top/daily/"


@dataclass(slots=True)
class HabrNewsEntry:
    title: str
    url: str


class HabrNewsService:
    def __init__(self, http_client: HttpClient) -> None:
        self.http_client = http_client

    def get_daily_news(self, limit: int = 10) -> list[HabrNewsEntry]:
        page_html = self.http_client.get_text(HABR_DAILY_NEWS_URL)
        entries = self._parse_entries(page_html)
        unique_entries: list[HabrNewsEntry] = []
        seen_urls: set[str] = set()

        for entry in entries:
            if entry.url in seen_urls:
                continue
            seen_urls.add(entry.url)
            unique_entries.append(entry)
            if len(unique_entries) >= limit:
                break

        return unique_entries

    def _parse_entries(self, page_html: str) -> list[HabrNewsEntry]:
        anchor_pattern = re.compile(
            r"<a(?P<attrs>[^>]+)>(?P<title>.*?)</a>",
            re.IGNORECASE | re.DOTALL,
        )
        entries: list[HabrNewsEntry] = []
        for match in anchor_pattern.finditer(page_html):
            attrs = match.group("attrs")
            href_match = re.search(
                r'href="(?P<href>/ru/news/\d+/|https://habr\.com/ru/news/\d+/)"',
                attrs,
                re.IGNORECASE,
            )
            if href_match is None:
                continue

            class_match = re.search(
                r'class="(?P<class>[^"]+)"',
                attrs,
                re.IGNORECASE,
            )
            class_value = class_match.group("class").lower() if class_match else ""
            if not any(
                token in class_value
                for token in ("tm-title__link", "tm-article-snippet__title-link")
            ):
                continue

            raw_title = match.group("title")
            title = self._clean_html(raw_title)
            if not title:
                continue

            href = html.unescape(href_match.group("href").strip())
            if href.startswith("/"):
                href = f"https://habr.com{href}"

            entries.append(HabrNewsEntry(title=title, url=href))

        return entries

    @staticmethod
    def _clean_html(value: str) -> str:
        without_tags = re.sub(r"<[^>]+>", " ", value)
        normalized = html.unescape(without_tags)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()
