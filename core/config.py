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