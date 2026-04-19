from __future__ import annotations

import platform
import subprocess
from typing import Any

from tools.base import BaseTool

try:
    import ctypes
except ImportError:
    ctypes = None


class SystemPowerTool(BaseTool):
    name = "system_power"
    description = "Управляет питанием Windows: переводит компьютер в сон или выключает его."
    risk_level = "confirm"

    def run(self, args: dict[str, Any]) -> str:
        action = str(args.get("action", "")).strip().lower()

        if platform.system().lower() != "windows":
            return "Команда управления питанием сейчас поддерживается только на Windows."

        if action == "sleep":
            return self._sleep()

        if action == "shutdown":
            return self._shutdown()

        return "Не удалось выполнить команду питания: неизвестное действие."

    def _sleep(self) -> str:
        if ctypes is None:
            raise RuntimeError("ctypes недоступен.")

        result = ctypes.windll.powrprof.SetSuspendState(False, True, False)
        if result == 0:
            raise RuntimeError("Windows не разрешила перевод в сон.")

        return "Перевожу компьютер в спящий режим."

    def _shutdown(self) -> str:
        completed = subprocess.run(
            ["shutdown", "/s", "/t", "0"],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or completed.stdout.strip()
            details = f" {stderr}" if stderr else ""
            raise RuntimeError(f"Не удалось выключить компьютер.{details}")

        return "Выключаю компьютер."
