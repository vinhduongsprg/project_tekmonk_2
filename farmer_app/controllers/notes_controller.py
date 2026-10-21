"""
Notes Controller
Handles notes for UI pages.
"""

from typing import List, Dict

from services.notes_service import NotesService


class NotesController:
    """Controller for notes data."""

    def __init__(self):
        self.service = NotesService()

    def get_all_notes(self) -> List[Dict]:
        return self.service.get_all_notes()

    def search_notes(self, query: str) -> List[Dict]:
        return self.service.search_notes(query)

    def add_note(self, note: Dict) -> bool:
        return self.service.add_note(note)

    def update_note(self, note: Dict) -> bool:
        return self.service.update_note(note)

    def delete_note(self, note_id: str) -> bool:
        return self.service.delete_note(note_id)
