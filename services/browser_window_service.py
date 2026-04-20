from __future__ import annotations

import ctypes
import time
import tkinter as tk


class BrowserWindowService:
    SW_RESTORE = 9
    KEYEVENTF_KEYUP = 0x0002

    VK_CONTROL = 0x11
    VK_F = 0x46
    VK_V = 0x56
    VK_RETURN = 0x0D
    VK_ESCAPE = 0x1B

    DEFAULT_BROWSER_HINTS = [
        "habr",
        "chrome",
        "edge",
        "browser",
        "firefox",
        "opera",
        "yandex",
    ]

    def __init__(self) -> None:
        self.user32 = ctypes.windll.user32

    def bring_to_front(
        self,
        title_hints: list[str] | None = None,
        timeout_seconds: float = 3.0,
    ) -> bool:
        deadline = time.time() + max(0.2, timeout_seconds)
        hints = [hint.lower() for hint in (title_hints or self.DEFAULT_BROWSER_HINTS)]

        while time.time() < deadline:
            hwnd = self._find_window(hints)
            if hwnd:
                if self.user32.IsIconic(hwnd):
                    self.user32.ShowWindow(hwnd, self.SW_RESTORE)
                    time.sleep(0.05)

                self.user32.SetForegroundWindow(hwnd)
                time.sleep(0.1)
                return True

            time.sleep(0.2)

        return False

    def scroll_to_text(
        self,
        text: str,
        title_hints: list[str] | None = None,
    ) -> bool:
        if not text.strip():
            return False

        if not self.bring_to_front(title_hints=title_hints):
            return False

        self._set_clipboard_text(text)
        time.sleep(0.05)
        self._press_combo(self.VK_CONTROL, self.VK_F)
        time.sleep(0.15)
        self._press_combo(self.VK_CONTROL, self.VK_V)
        time.sleep(0.15)
        self._press_key(self.VK_RETURN)
        time.sleep(0.35)
        self._press_key(self.VK_ESCAPE)
        return True

    def _find_window(self, hints: list[str]) -> int | None:
        matches: list[tuple[int, str]] = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def enum_proc(hwnd, _lparam):
            if not self.user32.IsWindowVisible(hwnd):
                return True

            length = self.user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True

            buffer = ctypes.create_unicode_buffer(length + 1)
            self.user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value.strip()
            if not title:
                return True

            lowered = title.lower()
            if any(hint in lowered for hint in hints):
                matches.append((int(hwnd), title))

            return True

        self.user32.EnumWindows(enum_proc, 0)
        if not matches:
            return None

        matches.sort(key=lambda item: self._window_rank(item[1], hints), reverse=True)
        return matches[0][0]

    @staticmethod
    def _window_rank(title: str, hints: list[str]) -> int:
        lowered = title.lower()
        rank = 0
        for hint in hints:
            if hint in lowered:
                rank += 10
        if "habr" in lowered:
            rank += 100
        return rank

    def _press_combo(self, modifier_vk: int, key_vk: int) -> None:
        self.user32.keybd_event(modifier_vk, 0, 0, 0)
        time.sleep(0.03)
        self.user32.keybd_event(key_vk, 0, 0, 0)
        time.sleep(0.03)
        self.user32.keybd_event(key_vk, 0, self.KEYEVENTF_KEYUP, 0)
        time.sleep(0.03)
        self.user32.keybd_event(modifier_vk, 0, self.KEYEVENTF_KEYUP, 0)

    def _press_key(self, key_vk: int) -> None:
        self.user32.keybd_event(key_vk, 0, 0, 0)
        time.sleep(0.03)
        self.user32.keybd_event(key_vk, 0, self.KEYEVENTF_KEYUP, 0)

    @staticmethod
    def _set_clipboard_text(text: str) -> None:
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
