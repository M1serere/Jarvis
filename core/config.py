from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

APP_NAME = "Jarvis"
SESSION_LOG_FILE = LOGS_DIR / "session.log"

LogMode = Literal["DEBUG", "DEV", "PROD"]


def get_log_mode() -> LogMode:
    raw_mode = os.getenv("JARVIS_LOG_MODE", "DEV").upper()

    if raw_mode in {"DEBUG", "DEV", "PROD"}:
        return raw_mode  # type: ignore[return-value]

    return "DEV"


LOG_MODE: LogMode = get_log_mode()

WORKSPACE_DIR = BASE_DIR / "workspace"
WORKSPACE_DIR.mkdir(exist_ok=True)

HTTP_TIMEOUT_SECONDS = 10

DEFAULT_WEATHER_LATITUDE = 32.7767
DEFAULT_WEATHER_LONGITUDE = -96.7970
DEFAULT_WEATHER_LOCATION_NAME = "Dallas"

PROGRAMMING_NEWS_FEEDS = [
    "https://feeds.feedburner.com/PythonInsider",
    "https://hnrss.org/frontpage",
]

BRAIN_PROVIDER = os.getenv("JARVIS_BRAIN_PROVIDER", "ollama").lower()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "10m")