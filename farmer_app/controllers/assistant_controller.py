"""
Assistant Controller
Coordinates assistant requests between UI and service.
"""

from typing import Dict, List, Optional, Tuple

from services.assistant_service import AssistantService


class AssistantController:
    """Controller for AI assistant interactions."""

    def __init__(self):
        self.service = AssistantService()

    def send_message(
        self,
        text: str,
        history: List[Dict],
        prefer_offline: bool = False,
        show_sources: bool = True,
    ) -> Tuple[Optional[str], Optional[str]]:
        return self.service.send_message(
            text,
            history,
            prefer_offline=prefer_offline,
            show_sources=show_sources,
        )
