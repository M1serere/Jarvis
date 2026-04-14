from __future__ import annotations

import xml.etree.ElementTree as ET

from services.http_client import HttpClient


class NewsService:
    def __init__(self, http_client: HttpClient) -> None:
        self.http_client = http_client

    def get_top_headlines(self, feed_urls: list[str], limit: int = 5) -> list[str]:
        headlines: list[str] = []

        for feed_url in feed_urls:
            try:
                xml_text = self.http_client.get_text(feed_url)
                parsed = self._parse_rss_titles(xml_text)
                for title in parsed:
                    if title not in headlines:
                        headlines.append(title)
                    if len(headlines) >= limit:
                        return headlines
            except Exception:
                continue

        return headlines[:limit]

    def _parse_rss_titles(self, xml_text: str) -> list[str]:
        root = ET.fromstring(xml_text)
        titles: list[str] = []

        for item in root.findall(".//item/title"):
            if item.text:
                title = item.text.strip()
                if title:
                    titles.append(title)

        return titles