"""
Prices Service
Reads local prices.json for offline price display.
"""

from pathlib import Path
import json


class PricesService:
    def __init__(self):
        self.data_file = Path(__file__).parent.parent / "data" / "prices.json"
        self.data_file.parent.mkdir(exist_ok=True)
        if not self.data_file.exists():
            self._save_data({"last_updated": "", "items": []})

    def _load_data(self):
        try:
            return json.loads(self.data_file.read_text(encoding="utf-8"))
        except Exception:
            return {"last_updated": "", "items": []}

    def _save_data(self, data):
        self.data_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_prices(self):
        return self._load_data()

    def search_prices(self, query: str, category: str, region: str):
        data = self._load_data()
        items = data.get("items", [])
        q = (query or "").lower().strip()
        category = (category or "Tất cả").strip()
        region = (region or "Toàn quốc").strip()

        results = []
        for item in items:
            name = (item.get("name") or "").lower()
            item_category = item.get("category", "")
            item_region = item.get("region", "")
            if q and q not in name:
                continue
            if category != "Tất cả" and item_category != category:
                continue
            if region != "Toàn quốc" and item_region != region:
                continue
            results.append(item)
        return {"last_updated": data.get("last_updated", ""), "items": results}
