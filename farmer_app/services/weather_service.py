"""
Weather Service
Fetches weather data from WeatherAPI with caching.
"""

from typing import Dict, Optional
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import requests

from config import get_setting


class WeatherService:
    """Service for weather-related operations."""

    def __init__(self):
        self.base_url = "https://api.weatherapi.com/v1"
        self.cache_file = Path(__file__).parent.parent / "data" / "weather_cache.json"

    def get_api_key(self) -> Optional[str]:
        """Get API key from env or config."""
        return os.getenv("WEATHERAPI_KEY") or get_setting("weather.api_key")

    def _load_cache(self) -> Optional[Dict]:
        if not self.cache_file.exists():
            return None
        try:
            return json.loads(self.cache_file.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _save_cache(self, payload: Dict) -> None:
        try:
            self.cache_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _cache_age_minutes(self, cached_at: str) -> Optional[float]:
        try:
            cached_dt = datetime.fromisoformat(cached_at)
            if cached_dt.tzinfo is None:
                cached_dt = cached_dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            return (now - cached_dt).total_seconds() / 60.0
        except Exception:
            return None

    def get_current_weather(self, location: str, update_interval: int, force: bool = False) -> Dict:
        """Fetch current weather for a location with cache."""
        cached = self._load_cache()
        if cached and not force:
            age = self._cache_age_minutes(cached.get("cached_at", ""))
            cached["age_minutes"] = age
            cached["stale"] = age is None or age >= update_interval
            if age is not None and age < update_interval:
                cached["source"] = "cache"
                return cached

        api_key = self.get_api_key()
        if not api_key:
            if cached:
                cached["source"] = "cache"
                age = self._cache_age_minutes(cached.get("cached_at", ""))
                cached["age_minutes"] = age
                cached["stale"] = age is None or age >= update_interval
                cached["error"] = "missing_api_key"
                return cached
            return {"error": "missing_api_key"}

        try:
            response = requests.get(
                f"{self.base_url}/current.json",
                params={"key": api_key, "q": location, "aqi": "no"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            payload = {
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "location": data.get("location", {}),
                "current": data.get("current", {}),
                "source": "live",
                "age_minutes": 0.0,
                "stale": False,
            }
            self._save_cache(payload)
            return payload
        except requests.RequestException:
            if cached:
                cached["source"] = "cache"
                age = self._cache_age_minutes(cached.get("cached_at", ""))
                cached["age_minutes"] = age
                cached["stale"] = age is None or age >= update_interval
                cached["error"] = "request_failed"
                return cached
            return {"error": "request_failed"}
