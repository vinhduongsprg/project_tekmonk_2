"""
Notes Service
Stores and retrieves notes in local JSON.
"""

from typing import List, Dict
from pathlib import Path
import json
from datetime import datetime

from services.calendar_service import CalendarService


class NotesService:
    """Service for notes storage."""

    def __init__(self):
        self.data_file = Path(__file__).parent.parent / "data" / "notes.json"
        self.data_file.parent.mkdir(exist_ok=True)
        self.calendar_service = CalendarService()
        if not self.data_file.exists():
            self._save_data([])

    def _load_data(self) -> List[Dict]:
        try:
            data = json.loads(self.data_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data.get("notes", [])
            if isinstance(data, list):
                return data
            return []
        except Exception:
            return []

    def _save_data(self, items: List[Dict]) -> bool:
        try:
            payload = {
                "notes": items,
                "last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            }
            self.data_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return True
        except Exception:
            return False

    def get_all_notes(self) -> List[Dict]:
        return self._load_data()

    def search_notes(self, query: str) -> List[Dict]:
        q = (query or "").lower().strip()
        if not q:
            return self.get_all_notes()
        items = self._load_data()
        results = []
        for item in items:
            title = item.get("title", "").lower()
            content = item.get("content", "").lower()
            if q in title or q in content:
                results.append(item)
        return results

    def add_note(self, note: Dict) -> bool:
        items = self._load_data()
        items.append(note)
        saved = self._save_data(items)
        if saved:
            self.calendar_service.upsert_note_entry(note)
        return saved

    def update_note(self, note: Dict) -> bool:
        items = self._load_data()
        new_items = []
        updated = False
        for item in items:
            if item.get("id") == note.get("id"):
                new_items.append(note)
                updated = True
            else:
                new_items.append(item)
        if not updated:
            new_items.append(note)
        saved = self._save_data(new_items)
        if saved:
            self.calendar_service.upsert_note_entry(note)
        return saved

    def delete_note(self, note_id: str) -> bool:
        items = self._load_data()
        new_items = [item for item in items if item.get("id") != note_id]
        saved = self._save_data(new_items)
        if saved:
            self.calendar_service.delete_note_entry(note_id)
        return saved

    @staticmethod
    def generate_id(prefix: str = "note") -> str:
        return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
