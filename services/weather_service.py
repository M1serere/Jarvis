from __future__ import annotations

from urllib.parse import quote

from services.http_client import HttpClient


class WeatherService:
    BASE_URL = "https://wttr.in"

    def __init__(self, http_client: HttpClient) -> None:
        self.http_client = http_client

    def get_today_weather_summary(self, location_name: str) -> str:
        normalized_location = location_name.strip() or "Vladivostok"
        encoded_location = quote(normalized_location)

        data = self.http_client.get_json(
            f"{self.BASE_URL}/{encoded_location}",
            params={"format": "j1", "lang": "ru"},
        )

        current_list = data.get("current_condition", [])
        weather_list = data.get("weather", [])
        area_list = data.get("nearest_area", [])

        current = current_list[0] if current_list else {}
        today = weather_list[0] if weather_list else {}
        area = area_list[0] if area_list else {}

        display_name = normalized_location
        area_names = area.get("areaName", [])
        if area_names and isinstance(area_names[0], dict):
            display_name = area_names[0].get("value", normalized_location)

        weather_desc_list = current.get("lang_ru") or current.get("weatherDesc") or []
        description = "без уточнения"
        if weather_desc_list and isinstance(weather_desc_list[0], dict):
            description = weather_desc_list[0].get("value", description)

        current_temp = current.get("temp_C", "?")
        feels_like = current.get("FeelsLikeC", "?")
        wind_speed = current.get("windspeedKmph", "?")
        max_temp = today.get("maxtempC", "?")
        min_temp = today.get("mintempC", "?")

        return (
            f"Погода сегодня в {display_name}: "
            f"сейчас {current_temp}°C, ощущается как {feels_like}°C, {description}, "
            f"днем до {max_temp}°C, ночью до {min_temp}°C, "
            f"ветер {wind_speed} км/ч."
        )
