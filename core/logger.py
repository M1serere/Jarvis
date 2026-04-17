# from __future__ import annotations

# import logging
# from logging import Logger

# from core.config import LOG_MODE, SESSION_LOG_FILE


# class MaxLevelFilter(logging.Filter):
#     def __init__(self, max_level: int) -> None:
#         super().__init__()
#         self.max_level = max_level

#     def filter(self, record: logging.LogRecord) -> bool:
#         return record.levelno <= self.max_level


# def setup_logger(name: str = "jarvis") -> Logger:
#     logger = logging.getLogger(name)

#     if logger.handlers:
#         return logger

#     logger.setLevel(logging.DEBUG)
#     logger.propagate = False

#     file_formatter = logging.Formatter(
#         fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
#     )

#     console_formatter = logging.Formatter(
#         fmt="%(levelname)s | %(message)s"
#     )

#     file_handler = logging.FileHandler(SESSION_LOG_FILE, encoding="utf-8")
#     file_handler.setLevel(logging.DEBUG)
#     file_handler.setFormatter(file_formatter)
#     logger.addHandler(file_handler)

#     if LOG_MODE == "DEBUG":
#         console_handler = logging.StreamHandler()
#         console_handler.setLevel(logging.DEBUG)
#         console_handler.setFormatter(file_formatter)
#         logger.addHandler(console_handler)

#     elif LOG_MODE == "DEV":
#         console_handler = logging.StreamHandler()
#         console_handler.setLevel(logging.INFO)
#         console_handler.setFormatter(console_formatter)
#         logger.addHandler(console_handler)

#     elif LOG_MODE == "PROD":
#         console_handler = logging.StreamHandler()
#         console_handler.setLevel(logging.WARNING)
#         console_handler.setFormatter(console_formatter)
#         logger.addHandler(console_handler)

#     return logger

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from logging import Logger
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from core.config import LOG_MODE, LOG_RETENTION_DAYS, LOG_FILE_NAME, LOGS_DIR


class CleanupTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(
        self,
        filename: str,
        when: str = "midnight",
        interval: int = 1,
        backupCount: int = 0,
        encoding: str | None = "utf-8",
    ) -> None:
        super().__init__(
            filename=filename,
            when=when,
            interval=interval,
            backupCount=backupCount,
            encoding=encoding,
        )

    def doRollover(self) -> None:
        super().doRollover()
        self._cleanup_old_logs()

    def _cleanup_old_logs(self) -> None:
        log_dir = Path(self.baseFilename).parent
        cutoff = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)

        for file_path in log_dir.glob(f"{LOG_FILE_NAME}*"):
            try:
                if not file_path.is_file():
                    continue

                modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                if modified < cutoff:
                    file_path.unlink(missing_ok=True)
            except Exception:
                # Логгер не должен падать из-за проблем с очисткой
                continue


def setup_logger(name: str = "jarvis") -> Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_formatter = logging.Formatter(
        fmt="%(levelname)s | %(message)s"
    )

    log_file = LOGS_DIR / LOG_FILE_NAME

    file_handler = CleanupTimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",
        interval=1,
        backupCount=0,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Однократная очистка и при старте
    try:
        file_handler._cleanup_old_logs()
    except Exception:
        pass

    if LOG_MODE == "DEBUG":
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(file_formatter)
        logger.addHandler(console_handler)

    elif LOG_MODE == "DEV":
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    elif LOG_MODE == "PROD":
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger