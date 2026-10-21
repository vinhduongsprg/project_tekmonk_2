"""
Prices Controller
"""

from services.prices_service import PricesService


class PricesController:
    def __init__(self):
        self.service = PricesService()

    def get_prices(self):
        return self.service.load_prices()

    def search_prices(self, query: str, category: str, region: str):
        return self.service.search_prices(query, category, region)
