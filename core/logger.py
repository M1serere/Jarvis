from __future__ import annotations

import logging
from datetime import datetime, timedelta
from logging import Logger
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from core.config import (
    LOG_CLEANUP_INTERVAL_DAYS,
    LOG_MODE,
    LOG_RETENTION_DAYS,
    LOG_FILE_NAME,
    LOGS_DIR,
)


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
        if not self._should_run_cleanup():
            return

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
                # Logger cleanup should never break the app.
                continue

        self._update_cleanup_timestamp()

    def _should_run_cleanup(self) -> bool:
        stamp_file = self._cleanup_stamp_file

        try:
            last_cleanup = datetime.fromtimestamp(stamp_file.stat().st_mtime)
        except FileNotFoundError:
            return True
        except Exception:
            return True

        return datetime.now() - last_cleanup >= timedelta(days=LOG_CLEANUP_INTERVAL_DAYS)

    def _update_cleanup_timestamp(self) -> None:
        stamp_file = self._cleanup_stamp_file
        stamp_file.parent.mkdir(parents=True, exist_ok=True)
        stamp_file.touch(exist_ok=True)

    @property
    def _cleanup_stamp_file(self) -> Path:
        return Path(self.baseFilename).parent / ".log_cleanup"


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

    # Run cleanup at startup only when the weekly interval has elapsed.
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
