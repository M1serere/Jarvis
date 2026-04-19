from __future__ import annotations

import time
from typing import Any

from tools.base import BaseTool

try:
    import ctypes
except ImportError:
    ctypes = None


class WindowControlTool(BaseTool):
    name = "window_control"
    description = (
        "Управляет окнами Windows: сворачивает все окна, восстанавливает "
        "свернутые окна и показывает рабочий стол."
    )
    risk_level = "safe"

    VK_LWIN = 0x5B
    VK_SHIFT = 0x10
    VK_D = 0x44
    VK_M = 0x4D
    KEYEVENTF_KEYUP = 0x0002

    SW_RESTORE = 9

    def run(self, args: dict[str, Any]) -> str:
        action = str(args.get("action", "")).strip().lower()

        if action in {"minimize_all", "minimize_windows"}:
            self._press_win_combo(self.VK_M)
            return "Сворачиваю все окна."

        if action == "show_desktop":
            self._press_win_combo(self.VK_D)
            return "Показываю рабочий стол."

        if action in {"restore_all", "restore_windows", "expand_all"}:
            restored = self._restore_windows()
            if restored == 0:
                return "Не нашёл свернутых окон для разворачивания."
            return f"Разворачиваю окна. Восстановлено: {restored}."

        return "Не удалось выполнить команду для окон: неизвестное действие."

    def _press_win_combo(self, key_vk: int) -> None:
        if ctypes is None:
            raise RuntimeError("ctypes недоступен.")

        user32 = ctypes.windll.user32
        user32.keybd_event(self.VK_LWIN, 0, 0, 0)
        time.sleep(0.03)
        user32.keybd_event(key_vk, 0, 0, 0)
        time.sleep(0.03)
        user32.keybd_event(key_vk, 0, self.KEYEVENTF_KEYUP, 0)
        time.sleep(0.03)
        user32.keybd_event(self.VK_LWIN, 0, self.KEYEVENTF_KEYUP, 0)

    def _restore_windows(self) -> int:
        if ctypes is None:
            raise RuntimeError("ctypes недоступен.")

        user32 = ctypes.windll.user32
        restored = 0

        enum_proc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_void_p,
            ctypes.c_void_p,
        )

        def callback(hwnd, _lparam):
            nonlocal restored

            if not user32.IsWindowVisible(hwnd):
                return True

            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, self.SW_RESTORE)
                restored += 1

            return True

        user32.EnumWindows(enum_proc(callback), 0)
        return restored
