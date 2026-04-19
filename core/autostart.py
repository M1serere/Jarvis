from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    import winreg
except ImportError:  # pragma: no cover
    winreg = None  # type: ignore[assignment]

from core.config import APP_NAME, PROJECT_DIR


RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_APPROVED_RUN_KEY_PATH = (
    r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
)
STARTUP_APPROVED_ENABLED = b"\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"


def _build_launch_command() -> str:
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()
        return f'"{executable}"'

    packaged_executable = _find_packaged_executable()
    if packaged_executable is not None:
        return f'"{packaged_executable}"'

    python_executable = Path(sys.executable).resolve()
    main_script = (PROJECT_DIR / "main.py").resolve()
    return f'"{python_executable}" "{main_script}"'


def _find_packaged_executable() -> Path | None:
    candidates = (
        PROJECT_DIR / "dist" / "Jarvis.exe",
        PROJECT_DIR / "dist" / "Jarvis" / "Jarvis.exe",
    )

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()

    return None


def is_supported() -> bool:
    return os.name == "nt" and winreg is not None


def is_enabled() -> bool:
    if not is_supported():
        return False

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            return value == _build_launch_command()
    except FileNotFoundError:
        return False
    except OSError:
        return False


def set_enabled(enabled: bool) -> bool:
    if not is_supported():
        return False

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY_PATH,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            if enabled:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _build_launch_command())
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, STARTUP_APPROVED_RUN_KEY_PATH) as key:
            if enabled:
                winreg.SetValueEx(
                    key,
                    APP_NAME,
                    0,
                    winreg.REG_BINARY,
                    STARTUP_APPROVED_ENABLED,
                )
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        return False
