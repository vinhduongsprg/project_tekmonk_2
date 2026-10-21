"""
Translation Utilities
Provides simple dictionary-based translations for API text.
"""

from __future__ import annotations

from pathlib import Path
import json
import re
from functools import lru_cache
from typing import Dict, Optional


_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "translations"


def _normalize_key(text: str) -> str:
    if not text:
        return ""
    cleaned = text.strip().lower()
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned


@lru_cache(maxsize=4)
def _load_translation_map(filename: str) -> Dict[str, str]:
    path = _DATA_DIR / filename
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def translate_weather_condition(text: str) -> str:
    """
    Translate a WeatherAPI condition string into Vietnamese.
    Falls back to the original text if not found.
    """
    if not text:
        return text
    mapping = _load_translation_map("weather.json")
    key = _normalize_key(text)
    return mapping.get(key, text)
