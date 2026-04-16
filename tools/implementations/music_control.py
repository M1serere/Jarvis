from __future__ import annotations

import os
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Any

from core.config import (
    DEFAULT_YOUTUBE_MUSIC_URL,
    YANDEX_MUSIC_LAUNCH_TARGET,
    YANDEX_MUSIC_WAVE_URL,
)
from tools.base import BaseTool

try:
    import ctypes
except ImportError:  # на всякий случай
    ctypes = None


class MusicControlTool(BaseTool):
    name = "music_control"
    description = (
        "Управляет музыкой: запускает YouTube, открывает Яндекс Музыку "
        "или переключает воспроизведение."
    )
    risk_level = "safe"

    VK_MEDIA_PLAY_PAUSE = 0xB3

    def run(self, args: dict[str, Any]) -> str:
        action = str(args.get("action", "")).strip().lower()
        source = str(args.get("source", "")).strip().lower()

        if action in {"pause", "stop", "play_pause", "toggle"}:
            self._send_media_play_pause()
            return "Переключаю воспроизведение музыки."

        if action == "play":
            if source == "youtube":
                return self._play_youtube()

            if source == "yandex_music":
                return self._play_yandex_music()

            return "Не удалось запустить музыку: источник не указан."

        return "Не удалось выполнить команду музыки: неизвестное действие."

    def _play_youtube(self) -> str:
        webbrowser.open(DEFAULT_YOUTUBE_MUSIC_URL)
        return "Запускаю музыку на YouTube."

    def _play_yandex_music(self) -> str:
        if not YANDEX_MUSIC_LAUNCH_TARGET and not YANDEX_MUSIC_WAVE_URL:
            return (
                "Не настроен запуск Яндекс Музыки. "
                "Укажи YANDEX_MUSIC_LAUNCH_TARGET или YANDEX_MUSIC_WAVE_URL в конфиге."
            )

        if YANDEX_MUSIC_LAUNCH_TARGET:
            launched = self._launch_target(YANDEX_MUSIC_LAUNCH_TARGET)
            if not launched:
                return "Не удалось открыть Яндекс Музыку."

            time.sleep(2)

        if YANDEX_MUSIC_WAVE_URL:
            webbrowser.open(YANDEX_MUSIC_WAVE_URL)
            return "Открываю Яндекс Музыку и пытаюсь открыть Мою волну."

        self._send_media_play_pause()
        return "Открываю Яндекс Музыку и пытаюсь запустить Мою волну."

    def _launch_target(self, target: str) -> bool:
        target = target.strip()
        if not target:
            return False

        if target.startswith(("http://", "https://", "yandexmusic://")):
            webbrowser.open(target)
            return True

        path = Path(target)
        if path.exists():
            suffix = path.suffix.lower()

            if suffix in {".bat", ".cmd"}:
                subprocess.Popen([str(path)], shell=True)
                return True

            if suffix == ".ps1":
                subprocess.Popen(
                    [
                        "powershell",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(path),
                    ],
                    shell=False,
                )
                return True

            os.startfile(str(path))  # type: ignore[attr-defined]
            return True

        return False

    def _send_media_play_pause(self) -> None:
        if ctypes is None:
            return

        user32 = ctypes.windll.user32
        user32.keybd_event(self.VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        user32.keybd_event(self.VK_MEDIA_PLAY_PAUSE, 0, 2, 0)