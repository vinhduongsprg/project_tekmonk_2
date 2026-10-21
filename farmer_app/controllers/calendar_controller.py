"""
Calendar Controller
Handles calendar entries for UI.
"""

from typing import List, Dict

from services.calendar_service import CalendarService


class CalendarController:
    """Controller for calendar data."""

    def __init__(self):
        self.service = CalendarService()

    def get_entries_for_date(self, date_str: str) -> List[Dict]:
        return self.service.get_entries_for_date(date_str)

    def search_entries(self, query: str) -> List[Dict]:
        return self.service.search_entries(query)

    def add_entry(self, entry: Dict) -> bool:
        return self.service.add_entry(entry)

    def delete_entry(self, entry_id: str) -> bool:
        return self.service.delete_entry(entry_id)
