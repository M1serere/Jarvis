from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal

PROJECT_DIR = Path(__file__).resolve().parent.parent


def _resolve_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "Jarvis"

        return Path.home() / "AppData" / "Local" / "Jarvis"

    return PROJECT_DIR


BASE_DIR = _resolve_base_dir()
BASE_DIR.mkdir(parents=True, exist_ok=True)

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

WORK_TIMER_HOURS = float(os.getenv("JARVIS_WORK_TIMER_HOURS", "3"))
WORK_TIMER_SECONDS = int(WORK_TIMER_HOURS * 60 * 60)

DEFAULT_WEATHER_LOCATION_NAME = os.getenv("JARVIS_WEATHER_LOCATION", "Vladivostok")

PROGRAMMING_NEWS_FEEDS = [
    "https://feeds.feedburner.com/PythonInsider",
    "https://hnrss.org/frontpage",
]

BRAIN_PROVIDER = os.getenv("JARVIS_BRAIN_PROVIDER", "ollama").lower()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
#OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:0.6b")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "10m")

DEFAULT_USER_NAME = "Госпожа"

# DEFAULT_YOUTUBE_MUSIC_URL = "https://www.youtube.com/watch?v=de4zk7OiwuI"

YOUTUBE_MUSIC_SEARCH_QUERY = "музыка для работы"
YOUTUBE_MUSIC_MIN_DURATION_SECONDS = 3600
YOUTUBE_MUSIC_SEARCH_CANDIDATES = 10
YOUTUBE_MUSIC_FALLBACK_RESULTS = 30

LOG_RETENTION_DAYS = 180
LOG_FILE_NAME = "jarvis.log"

UI_WINDOW_TITLE = "Jarvis Status"

TTS_PROVIDER = os.getenv("JARVIS_TTS_PROVIDER", "edge").lower()

# Основной голос для edge-tts.
# Попробуй сначала Dmitry. Если не понравится — потом можно быстро поменять.
EDGE_TTS_VOICE = os.getenv("JARVIS_EDGE_TTS_VOICE", "ru-RU-DmitryNeural")

# Для "вайба Джарвиса" лучше чуть медленнее и немного ниже по тону.
EDGE_TTS_RATE = os.getenv("JARVIS_EDGE_TTS_RATE", "-8%")
EDGE_TTS_PITCH = os.getenv("JARVIS_EDGE_TTS_PITCH", "-8Hz")

# Локальный fallback, если интернет/edge-tts недоступен
PYTTSX3_RATE = int(os.getenv("JARVIS_PYTTSX3_RATE", "170"))

TTS_TEMP_DIR = BASE_DIR / "temp_tts"
TTS_TEMP_DIR.mkdir(exist_ok=True)
