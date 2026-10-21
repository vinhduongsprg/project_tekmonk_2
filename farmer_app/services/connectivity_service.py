"""
Connectivity Service
Checks whether the app has internet access.
"""

from typing import Optional
import requests


class ConnectivityService:
    """Service for connectivity checks."""

    def __init__(self):
        self.test_url = "https://clients3.google.com/generate_204"
        self.timeout = 5

    def is_online(self) -> bool:
        try:
            resp = requests.get(self.test_url, timeout=self.timeout)
            return resp.status_code == 204
        except requests.RequestException:
            return False
