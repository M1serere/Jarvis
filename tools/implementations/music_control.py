from __future__ import annotations

import webbrowser
from typing import Any

from core.config import DEFAULT_YOUTUBE_MUSIC_URL
from tools.base import BaseTool

try:
    import ctypes
except ImportError:  # на всякий случай
    ctypes = None


class MusicControlTool(BaseTool):
    name = "music_control"
    description = (
        "Управляет музыкой: запускает YouTube "
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

            return "Не удалось запустить музыку: источник не указан."

        return "Не удалось выполнить команду музыки: неизвестное действие."

    def _play_youtube(self) -> str:
        webbrowser.open(DEFAULT_YOUTUBE_MUSIC_URL)
        return "Запускаю музыку на YouTube."

    def _send_media_play_pause(self) -> None:
        if ctypes is None:
            return

        user32 = ctypes.windll.user32
        user32.keybd_event(self.VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        user32.keybd_event(self.VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
