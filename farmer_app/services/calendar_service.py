"""
Calendar Service
Stores and retrieves calendar entries in local JSON.
"""

from typing import List, Dict
from pathlib import Path
import json
from datetime import datetime


class CalendarService:
    """Service for calendar storage."""

    def __init__(self):
        self.data_file = Path(__file__).parent.parent / "data" / "calendar.json"
        self.data_file.parent.mkdir(exist_ok=True)
        if not self.data_file.exists():
            self._save_data([])

    def _load_data(self) -> List[Dict]:
        try:
            return json.loads(self.data_file.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save_data(self, items: List[Dict]) -> bool:
        try:
            self.data_file.write_text(
                json.dumps(items, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return True
        except Exception:
            return False

    def get_entries_for_date(self, date_str: str) -> List[Dict]:
        items = self._load_data()
        return [item for item in items if item.get("date") == date_str]

    def search_entries(self, query: str) -> List[Dict]:
        q = (query or "").lower().strip()
        if not q:
            return []
        items = self._load_data()
        results = []
        for item in items:
            if q in (item.get("title", "").lower() or "") or q in (item.get("note", "").lower() or ""):
                results.append(item)
        return results

    def add_entry(self, entry: Dict) -> bool:
        items = self._load_data()
        items.append(entry)
        return self._save_data(items)

    def delete_entry(self, entry_id: str) -> bool:
        items = self._load_data()
        new_items = [item for item in items if item.get("id") != entry_id]
        return self._save_data(new_items)

    def upsert_note_entry(self, note: Dict) -> bool:
        """Create or update a calendar entry for a linked note."""
        note_id = note.get("id")
        linked_date = note.get("linked_date")
        items = self._load_data()
        existing = None
        for item in items:
            if item.get("note_id") == note_id:
                existing = item
                break
        # Remove existing note entries
        items = [item for item in items if item.get("note_id") != note_id]
        if linked_date:
            entry = {
                "id": f"note_{note_id}",
                "note_id": note_id,
                "date": linked_date,
                "title": note.get("title", "Ghi chú"),
                "time": existing.get("time", "") if existing else "",
                "type": "Note",
                "repeat": existing.get("repeat", "none") if existing else "none",
                "note": note.get("content", ""),
                "created_at": note.get("created_at"),
                "updated_at": note.get("updated_at"),
            }
            items.append(entry)
        return self._save_data(items)

    def delete_note_entry(self, note_id: str) -> bool:
        """Remove calendar entries linked to a note."""
        items = self._load_data()
        new_items = [item for item in items if item.get("note_id") != note_id]
        return self._save_data(new_items)

    @staticmethod
    def generate_id(prefix: str = "entry") -> str:
        return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
