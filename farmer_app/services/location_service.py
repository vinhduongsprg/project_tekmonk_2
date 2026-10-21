"""
Location Service
Handles location data and geographic operations
"""

from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path


class LocationService:
    """Service for location-related operations"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self._load_province_data()
        
    def _load_province_data(self):
        """Load province and region data"""
        # Vietnamese provinces by region
        self.provinces_by_region = {
            "Miền Bắc": [
                "Hà Nội", "Hải Phòng", "Bắc Giang", "Bắc Kạn", "Bắc Ninh",
                "Cao Bằng", "Điện Biên", "Hà Giang", "Hà Nam",
                "Hải Dương", "Hòa Bình", "Hưng Yên", "Lai Châu", "Lạng Sơn",
                "Lào Cai", "Nam Định", "Ninh Bình", "Phú Thọ", "Quảng Bình",
                "Quảng Ninh", "Sơn La", "Thái Bình", "Thái Nguyên", "Thanh Hóa",
                "Tuyên Quang", "Vĩnh Phúc", "Yên Bái"
            ],
            "Miền Trung": [
                "Đà Nẵng", "Bình Định", "Bình Thuận", "Đắk Lắk", "Đắk Nông",
                "Gia Lai", "Hà Tĩnh", "Khánh Hòa", "Kon Tum", "Lâm Đồng",
                "Nghệ An", "Ninh Thuận", "Phú Yên", "Quảng Nam", "Quảng Ngãi",
                "Quảng Trị", "Thanh Hóa", "Thừa Thiên Huế"
            ],
            "Miền Nam": [
                "Hồ Chí Minh", "Cần Thơ", "An Giang", "Bà Rịa - Vũng Tàu",
                "Bạc Liêu", "Bến Tre", "Bình Dương", "Bình Phước", "Cà Mau",
                "Đồng Nai", "Đồng Tháp", "Hậu Giang", "Kiên Giang", "Long An",
                "Sóc Trăng", "Tây Ninh", "Tiền Giang", "Trà Vinh", "Vĩnh Long"
            ]
        }
        
        # Province coordinates (approximate)
        self.province_coordinates = {
            "Hà Nội": (21.0285, 105.8542),
            "Hồ Chí Minh": (10.8231, 106.6297),
            "Đà Nẵng": (16.0544, 108.2022),
            "Hải Phòng": (20.8449, 106.6881),
            "Cần Thơ": (10.0452, 105.7469),
            "An Giang": (10.3675, 105.4322),
            "Bà Rịa - Vũng Tàu": (10.3460, 107.0843),
            "Bắc Giang": (21.2731, 106.1946),
            "Bắc Kạn": (22.1470, 105.8345),
            "Bạc Liêu": (9.2935, 105.7275),
            "Bắc Ninh": (21.1864, 106.0763),
            "Bến Tre": (10.2417, 106.3755),
            "Bình Định": (13.7764, 109.2236),
            "Bình Dương": (11.1254, 106.6586),
            "Bình Phước": (11.6165, 106.8457),
            "Bình Thuận": (10.9310, 107.2195),
            "Cà Mau": (9.1769, 105.1495),
            "Cao Bằng": (22.6657, 106.2574),
            "Đắk Lắk": (12.6667, 108.1667),
            "Đắk Nông": (12.0833, 107.4667),
            "Điện Biên": (22.4167, 103.0000),
            "Đồng Nai": (10.7556, 106.8231),
            "Đồng Tháp": (10.4573, 105.6345),
            "Gia Lai": (13.4167, 108.0000),
            "Hà Giang": (22.8238, 104.9836),
            "Hà Nam": (20.5444, 106.0039),
            "Hà Tĩnh": (18.3428, 105.6905),
            "Hải Dương": (20.9444, 106.3333),
            "Hậu Giang": (9.7833, 105.9667),
            "Hòa Bình": (20.8167, 105.3333),
            "Hưng Yên": (20.6467, 106.0533),
            "Khánh Hòa": (12.2500, 109.0000),
            "Kiên Giang": (10.0167, 105.0833),
            "Kon Tum": (14.3500, 108.0000),
            "Lai Châu": (22.4000, 103.1667),
            "Lâm Đồng": (11.9167, 108.4167),
            "Lạng Sơn": (21.8500, 106.7500),
            "Lào Cai": (22.4833, 103.9833),
            "Long An": (10.5333, 106.4333),
            "Nam Định": (20.4167, 106.1667),
            "Nghệ An": (19.0000, 105.0000),
            "Ninh Bình": (20.2500, 105.7500),
            "Ninh Thuận": (11.5000, 108.6667),
            "Phú Thọ": (21.4167, 105.4167),
            "Phú Yên": (13.0833, 109.0833),
            "Quảng Bình": (17.5000, 106.2500),
            "Quảng Nam": (15.5000, 108.0000),
            "Quảng Ngãi": (15.5000, 108.7500),
            "Quảng Ninh": (21.0000, 107.5000),
            "Quảng Trị": (16.7500, 106.7500),
            "Sóc Trăng": (9.6000, 105.6667),
            "Sơn La": (21.1667, 103.9167),
            "Tây Ninh": (11.3167, 106.0833),
            "Thái Bình": (20.4167, 106.3333),
            "Thái Nguyên": (21.5833, 105.8333),
            "Thanh Hóa": (19.8000, 105.7833),
            "Thừa Thiên Huế": (16.4667, 107.5833),
            "Tiền Giang": (10.3667, 106.2167),
            "Trà Vinh": (9.9333, 106.3333),
            "Tuyên Quang": (21.7833, 105.2167),
            "Vĩnh Long": (10.2500, 105.9667),
            "Vĩnh Phúc": (21.3083, 105.6083),
            "Yên Bái": (21.7000, 104.9167)
        }
        
    def get_all_provinces(self) -> List[str]:
        """Get list of all provinces"""
        all_provinces = []
        for provinces in self.provinces_by_region.values():
            all_provinces.extend(provinces)
        return sorted(all_provinces)
        
    def get_region_from_province(self, province: str) -> Optional[str]:
        """Get region from province name"""
        for region, provinces in self.provinces_by_region.items():
            if province in provinces:
                return region
        return None
        
    def get_provinces_by_region(self, region: str) -> List[str]:
        """Get provinces in a specific region"""
        return self.provinces_by_region.get(region, [])
        
    def get_coordinates(self, province: str) -> Optional[Tuple[float, float]]:
        """Get coordinates for a province"""
        return self.province_coordinates.get(province)
        
    def search_provinces(self, query: str) -> List[str]:
        """Search provinces by name (case-insensitive)"""
        query_lower = query.lower()
        all_provinces = self.get_all_provinces()
        
        matches = []
        for province in all_provinces:
            if query_lower in province.lower():
                matches.append(province)
                
        return matches
        
    def validate_province(self, province: str) -> bool:
        """Check if province is valid"""
        return province in self.get_all_provinces()
        
    def get_location_info(self, province: str) -> Dict[str, any]:
        """Get complete location information for a province"""
        if not self.validate_province(province):
            return {}
            
        region = self.get_region_from_province(province)
        coordinates = self.get_coordinates(province)
        
        return {
            "province": province,
            "region": region,
            "coordinates": coordinates,
            "is_valid": True
        }
