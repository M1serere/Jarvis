from __future__ import annotations

from typing import Any

from services.http_client import HttpClient


class WeatherService:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, http_client: HttpClient) -> None:
        self.http_client = http_client

    def get_today_weather_summary(
        self,
        latitude: float,
        longitude: float,
        location_name: str,
    ) -> str:
        data = self.http_client.get_json(
            self.BASE_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,wind_speed_10m,weather_code",
                "daily": "temperature_2m_max,temperature_2m_min",
                "timezone": "auto",
                "forecast_days": 1,
            },
        )

        current = data.get("current", {})
        daily = data.get("daily", {})

        current_temp = current.get("temperature_2m")
        wind_speed = current.get("wind_speed_10m")

        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])

        max_temp = max_temps[0] if max_temps else "?"
        min_temp = min_temps[0] if min_temps else "?"

        return (
            f"Погода сегодня в {location_name}: "
            f"сейчас {current_temp}°C, "
            f"днём максимум {max_temp}°C, "
            f"ночью минимум {min_temp}°C, "
            f"ветер {wind_speed} км/ч."
        )