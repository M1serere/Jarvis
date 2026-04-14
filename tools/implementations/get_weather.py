from __future__ import annotations

from typing import Any

from core.config import (
    DEFAULT_WEATHER_LATITUDE,
    DEFAULT_WEATHER_LOCATION_NAME,
    DEFAULT_WEATHER_LONGITUDE,
    HTTP_TIMEOUT_SECONDS,
)
from services.http_client import HttpClient
from services.weather_service import WeatherService
from tools.base import BaseTool


class GetWeatherTool(BaseTool):
    name = "get_weather"
    description = "Получает текущую погоду на сегодня."
    risk_level = "safe"

    def __init__(self) -> None:
        http_client = HttpClient(timeout=HTTP_TIMEOUT_SECONDS)
        self.weather_service = WeatherService(http_client=http_client)

    def run(self, args: dict[str, Any]) -> str:
        latitude = float(args.get("latitude", DEFAULT_WEATHER_LATITUDE))
        longitude = float(args.get("longitude", DEFAULT_WEATHER_LONGITUDE))
        location_name = str(args.get("location_name", DEFAULT_WEATHER_LOCATION_NAME))

        try:
            return self.weather_service.get_today_weather_summary(
                latitude=latitude,
                longitude=longitude,
                location_name=location_name,
            )
        except Exception as exc:
            return f"Не удалось получить погоду: {exc}"