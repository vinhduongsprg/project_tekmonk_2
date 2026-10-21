"""
News Controller
Handles news requests for UI pages.
"""

from typing import Dict

from config import get_setting
from services.news_service import NewsService


class NewsController:
    """Controller for news data."""

    def __init__(self):
        self.service = NewsService()

    def get_news(self, force: bool = False) -> Dict:
        interval = int(get_setting("news.update_interval", 6))
        return self.service.get_news(interval, force=force)
