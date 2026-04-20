from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from core.config import BASE_DIR


SETTINGS_FILE = BASE_DIR / "settings.json"


@dataclass(slots=True)
class AppSettings:
    voice_volume: int = 80
    autostart_enabled: bool = True
    overlay_mode: bool = True
    installed_name_prompt_done: bool = False


class SettingsStore:
    def __init__(self) -> None:
        self._path = SETTINGS_FILE

    def load(self) -> AppSettings:
        try:
            if not self._path.exists():
                return AppSettings()

            data = json.loads(self._path.read_text(encoding="utf-8"))
            return AppSettings(
                voice_volume=self._clamp_volume(data.get("voice_volume", 80)),
                autostart_enabled=self._to_bool(data.get("autostart_enabled", True)),
                overlay_mode=self._to_bool(data.get("overlay_mode", True)),
                installed_name_prompt_done=self._to_bool(
                    data.get("installed_name_prompt_done", False)
                ),
            )
        except Exception:
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        payload = asdict(settings)
        payload["voice_volume"] = self._clamp_volume(payload.get("voice_volume", 80))
        payload["autostart_enabled"] = self._to_bool(
            payload.get("autostart_enabled", True)
        )
        payload["overlay_mode"] = self._to_bool(payload.get("overlay_mode", False))
        payload["installed_name_prompt_done"] = self._to_bool(
            payload.get("installed_name_prompt_done", False)
        )
        self._path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _clamp_volume(value: int | float) -> int:
        try:
            return max(0, min(int(float(value)), 100))
        except Exception:
            return 80

    @staticmethod
    def _to_bool(value: object) -> bool:
        return bool(value)
