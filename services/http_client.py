from __future__ import annotations

import json
from typing import Any

import requests


class HttpClient:
    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()

        # Many JSON APIs are UTF-8 even when the response encoding metadata is wrong.
        # Decode from raw bytes first so Cyrillic text does not turn into mojibake.
        try:
            return json.loads(response.content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return response.json()

    def get_text(self, url: str, params: dict[str, Any] | None = None) -> str:
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.text
