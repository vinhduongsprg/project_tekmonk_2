"""
Weather Controller
Handles weather requests for UI pages.
"""

from typing import Dict

from config import get_setting
from services.weather_service import WeatherService
from utils.translation_utils import translate_weather_condition


class WeatherController:
    """Controller for weather data."""

    def __init__(self):
        self.service = WeatherService()

    def get_default_location(self) -> str:
        province = get_setting("location.province")
        return province or "Hà Nội"

    def get_current_weather(self, location: str = "", force: bool = False) -> Dict:
        target = location or self.get_default_location()
        interval = int(get_setting("weather.update_interval", 30))
        data = self.service.get_current_weather(target, interval, force=force)
        current = data.get("current")
        if isinstance(current, dict):
            condition = current.get("condition")
            if isinstance(condition, dict):
                text = condition.get("text")
                if text:
                    condition["text"] = translate_weather_condition(text)
        return data
