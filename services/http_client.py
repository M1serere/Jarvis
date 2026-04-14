from __future__ import annotations

from typing import Any

import requests


class HttpClient:
    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_text(self, url: str, params: dict[str, Any] | None = None) -> str:
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.text