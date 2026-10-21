"""
News Service
Fetches RSS feeds and caches results.
"""

from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, timezone
import json

import feedparser

from config import get_setting


class NewsService:
    """Service for news-related operations."""

    def __init__(self):
        self.cache_file = Path(__file__).parent.parent / "data" / "news_cache.json"

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

    def _cache_age_hours(self, cached_at: str) -> Optional[float]:
        try:
            cached_dt = datetime.fromisoformat(cached_at)
            if cached_dt.tzinfo is None:
                cached_dt = cached_dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            return (now - cached_dt).total_seconds() / 3600.0
        except Exception:
            return None

    def _get_sources(self) -> List[str]:
        sources = get_setting("news.sources", [])
        if isinstance(sources, list):
            return [s for s in sources if isinstance(s, str) and s.strip()]
        return []

    def get_news(self, update_interval_hours: int, force: bool = False) -> Dict:
        cached = self._load_cache()
        if cached and not force:
            age = self._cache_age_hours(cached.get("cached_at", ""))
            cached["age_hours"] = age
            cached["stale"] = age is None or age >= update_interval_hours
            if age is not None and age < update_interval_hours:
                cached["source"] = "cache"
                return cached

        sources = self._get_sources()
        if not sources:
            if cached:
                cached["source"] = "cache"
                age = self._cache_age_hours(cached.get("cached_at", ""))
                cached["age_hours"] = age
                cached["stale"] = age is None or age >= update_interval_hours
                cached["error"] = "no_sources"
                return cached
            return {"error": "no_sources"}

        items: List[Dict] = []
        for url in sources:
            feed = feedparser.parse(url)
            source_name = feed.feed.get("title", "") if hasattr(feed, "feed") else ""
            for entry in feed.entries[:15]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "") or entry.get("description", "")
                link = entry.get("link", "")
                published = entry.get("published", "") or entry.get("updated", "")
                if not title:
                    continue
                items.append(
                    {
                        "title": title,
                        "summary": summary.strip(),
                        "link": link,
                        "published": published,
                        "source": source_name,
                    }
                )

        if not items and cached:
            cached["source"] = "cache"
            age = self._cache_age_hours(cached.get("cached_at", ""))
            cached["age_hours"] = age
            cached["stale"] = age is None or age >= update_interval_hours
            cached["error"] = "request_failed"
            return cached

        payload = {
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "items": items,
            "source": "live",
            "age_hours": 0.0,
            "stale": False,
        }
        self._save_cache(payload)
        return payload
