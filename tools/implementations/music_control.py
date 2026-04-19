from __future__ import annotations

import json
import random
import re
import webbrowser
from typing import Any
from urllib.parse import quote_plus

import requests

from core.config import (
    YOUTUBE_MUSIC_FALLBACK_RESULTS,
    YOUTUBE_MUSIC_MIN_DURATION_SECONDS,
    YOUTUBE_MUSIC_SEARCH_CANDIDATES,
    YOUTUBE_MUSIC_SEARCH_QUERY,
)
from tools.base import BaseTool

try:
    import ctypes
except ImportError:
    ctypes = None


class MusicControlTool(BaseTool):
    name = "music_control"
    description = (
        "Управляет музыкой: ищет длинные видео на YouTube "
        "или переключает воспроизведение."
    )
    risk_level = "safe"

    VK_MEDIA_PLAY_PAUSE = 0xB3
    YOUTUBE_SEARCH_URL = "https://www.youtube.com/results?search_query={query}"

    def run(self, args: dict[str, Any]) -> str:
        action = str(args.get("action", "")).strip().lower()
        source = str(args.get("source", "")).strip().lower()

        if action in {"pause", "stop", "play_pause", "toggle"}:
            self._send_media_play_pause()
            return "Переключаю воспроизведение музыки."

        if action == "play":
            if source == "youtube":
                return self._play_youtube()

            return "Не удалось запустить музыку: источник не указан."

        return "Не удалось выполнить команду музыки: неизвестное действие."

    def _play_youtube(self) -> str:
        try:
            videos = self._search_youtube_videos(YOUTUBE_MUSIC_SEARCH_QUERY)

            first_candidates = videos[:YOUTUBE_MUSIC_SEARCH_CANDIDATES]
            long_videos = [
                video
                for video in first_candidates
                if video["duration_seconds"] >= YOUTUBE_MUSIC_MIN_DURATION_SECONDS
            ]

            if not long_videos:
                fallback_candidates = videos[:YOUTUBE_MUSIC_FALLBACK_RESULTS]
                long_videos = [
                    video
                    for video in fallback_candidates
                    if video["duration_seconds"] >= YOUTUBE_MUSIC_MIN_DURATION_SECONDS
                ]

            if not long_videos:
                search_url = self.YOUTUBE_SEARCH_URL.format(
                    query=quote_plus(YOUTUBE_MUSIC_SEARCH_QUERY)
                )
                webbrowser.open(search_url)
                return (
                    "Не нашёл подходящее длинное видео автоматически, "
                    "поэтому просто открыл поиск YouTube."
                )

            selected_video = random.choice(long_videos)
            webbrowser.open(selected_video["url"])

            return (
                f"Запускаю музыку на YouTube: "
                f"{selected_video['title']} ({selected_video['duration_text']})."
            )
        except Exception:
            search_url = self.YOUTUBE_SEARCH_URL.format(
                query=quote_plus(YOUTUBE_MUSIC_SEARCH_QUERY)
            )
            webbrowser.open(search_url)
            return (
                "Не удалось автоматически выбрать видео, "
                "поэтому я открыл поиск YouTube."
            )

    def _search_youtube_videos(self, query: str) -> list[dict[str, Any]]:
        url = self.YOUTUBE_SEARCH_URL.format(query=quote_plus(query))
        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            },
            timeout=10,
        )
        response.raise_for_status()

        yt_data = self._extract_yt_initial_data(response.text)
        videos = self._extract_video_renderers(yt_data)

        unique_videos: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        for video in videos:
            video_id = video.get("videoId")
            if not video_id or video_id in seen_ids:
                continue

            duration_text = self._extract_duration_text(video)
            if not duration_text:
                continue

            duration_seconds = self._duration_to_seconds(duration_text)
            if duration_seconds <= 0:
                continue

            title = self._extract_title(video)
            if not title:
                title = "Без названия"

            unique_videos.append(
                {
                    "video_id": video_id,
                    "title": title,
                    "duration_text": duration_text,
                    "duration_seconds": duration_seconds,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                }
            )
            seen_ids.add(video_id)

        return unique_videos

    def _extract_yt_initial_data(self, html: str) -> dict[str, Any]:
        patterns = [
            r"var ytInitialData = (\{.*?\});",
            r"window\[['\"]ytInitialData['\"]\]\s*=\s*(\{.*?\});",
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                return json.loads(match.group(1))

        raise ValueError("Не удалось извлечь ytInitialData из страницы YouTube.")

    def _extract_video_renderers(self, data: Any) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                if "videoRenderer" in node and isinstance(node["videoRenderer"], dict):
                    result.append(node["videoRenderer"])

                for value in node.values():
                    walk(value)

            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(data)
        return result

    def _extract_title(self, video: dict[str, Any]) -> str:
        title_data = video.get("title", {})
        runs = title_data.get("runs", [])

        if runs:
            return "".join(str(run.get("text", "")) for run in runs).strip()

        return str(title_data.get("simpleText", "")).strip()

    def _extract_duration_text(self, video: dict[str, Any]) -> str | None:
        length_text = video.get("lengthText", {})

        if "simpleText" in length_text:
            return str(length_text["simpleText"]).strip()

        runs = length_text.get("runs", [])
        if runs:
            return "".join(str(run.get("text", "")) for run in runs).strip()

        return None

    def _duration_to_seconds(self, value: str) -> int:
        parts = value.strip().split(":")
        if not parts or not all(part.isdigit() for part in parts):
            return 0

        numbers = [int(part) for part in parts]

        if len(numbers) == 3:
            hours, minutes, seconds = numbers
            return hours * 3600 + minutes * 60 + seconds

        if len(numbers) == 2:
            minutes, seconds = numbers
            return minutes * 60 + seconds

        if len(numbers) == 1:
            return numbers[0]

        return 0

    def _send_media_play_pause(self) -> None:
        if ctypes is None:
            return

        user32 = ctypes.windll.user32
        user32.keybd_event(self.VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        user32.keybd_event(self.VK_MEDIA_PLAY_PAUSE, 0, 2, 0)