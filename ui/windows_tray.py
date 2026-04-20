from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw
import pystray


class WindowsTrayIcon:
    def __init__(
        self,
        tooltip: str,
        on_restore: Callable[[], None],
        on_exit: Callable[[], None],
        icon_path: str | None = None,
    ) -> None:
        self.tooltip = tooltip
        self.on_restore = on_restore
        self.on_exit = on_exit
        self.icon_path = icon_path

        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None
        self._started = False
        self._ready = threading.Event()

    def start(self) -> None:
        if self._started:
            return

        self._started = True
        self._thread = threading.Thread(target=self._run_icon, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=5)

    def stop(self) -> None:
        self._started = False
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None

    def is_available(self) -> bool:
        return self._started and self._icon is not None

    def _run_icon(self) -> None:
        image = self._load_image()

        menu = pystray.Menu(
            pystray.MenuItem("Open Jarvis", self._handle_restore),
            pystray.MenuItem("Exit", self._handle_exit),
        )

        self._icon = pystray.Icon("jarvis_tray", image, self.tooltip, menu)
        self._ready.set()

        try:
            self._icon.run()
        except Exception:
            self._icon = None
            self._started = False

    def _handle_restore(self, icon=None, item=None) -> None:
        try:
            self.on_restore()
        except Exception:
            pass

    def _handle_exit(self, icon=None, item=None) -> None:
        try:
            self.on_exit()
        except Exception:
            pass

    def _load_image(self) -> Image.Image:
        if self.icon_path:
            path = Path(self.icon_path)
            if path.exists():
                try:
                    return Image.open(path).convert("RGBA")
                except Exception:
                    pass

        # fallback-иконка, если файл не загрузился
        size = 64
        image = Image.new("RGBA", (size, size), (3, 19, 31, 0))
        draw = ImageDraw.Draw(image)

        # кольцо
        draw.ellipse((8, 8, 56, 56), outline=(105, 230, 255, 255), width=4)

        # буква J
        draw.line((38, 16, 38, 42), fill=(105, 230, 255, 255), width=5)
        draw.arc((18, 30, 38, 52), start=270, end=120, fill=(105, 230, 255, 255), width=5)

        return image