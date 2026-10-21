"""
Location Controller
Handles location-related operations between UI and Service layers
"""

from typing import Optional, Dict, Any
from PySide6.QtCore import Signal, QObject

from services.location_service import LocationService
from config import get_setting, set_setting


class LocationController(QObject):
    """Controller for location operations"""
    
    # Signals for UI updates
    location_changed = Signal(str, str)  # province, region
    location_error = Signal(str)  # error message
    location_saved = Signal()  # location successfully saved
    
    def __init__(self):
        super().__init__()
        self.location_service = LocationService()
        self.current_province = None
        self.current_region = None
        
    def load_saved_location(self) -> bool:
        """Load saved location from config"""
        try:
            province = get_setting('location.province')
            region = get_setting('location.region')
            
            if province and region:
                self.current_province = province
                self.current_region = region
                return True
            return False
        except Exception as e:
            self.location_error.emit(f"Lỗi khi tải vị trí: {str(e)}")
            return False
            
    def get_all_provinces(self):
        """Get list of all provinces"""
        try:
            return self.location_service.get_all_provinces()
        except Exception as e:
            self.location_error.emit(f"Lỗi khi lấy danh sách tỉnh: {str(e)}")
            return []
            
    def get_region_from_province(self, province: str) -> Optional[str]:
        """Get region from province"""
        try:
            return self.location_service.get_region_from_province(province)
        except Exception as e:
            self.location_error.emit(f"Lỗi khi xác định vùng: {str(e)}")
            return None
            
    def get_provinces_by_region(self, region: str):
        """Get provinces in a specific region"""
        try:
            return self.location_service.get_provinces_by_region(region)
        except Exception as e:
            self.location_error.emit(f"Lỗi khi lấy tỉnh theo vùng: {str(e)}")
            return []
            
    def search_provinces(self, query: str):
        """Search provinces by name"""
        try:
            return self.location_service.search_provinces(query)
        except Exception as e:
            self.location_error.emit(f"Lỗi khi tìm kiếm tỉnh: {str(e)}")
            return []
            
    def validate_province(self, province: str) -> bool:
        """Validate province name"""
        try:
            return self.location_service.validate_province(province)
        except Exception as e:
            self.location_error.emit(f"Lỗi khi xác thực tỉnh: {str(e)}")
            return False
            
    def get_coordinates(self, province: str) -> Optional[tuple]:
        """Get coordinates for province"""
        try:
            return self.location_service.get_coordinates(province)
        except Exception as e:
            self.location_error.emit(f"Lỗi khi lấy tọa độ: {str(e)}")
            return None
            
    def get_location_info(self, province: str) -> Dict[str, Any]:
        """Get complete location information"""
        try:
            return self.location_service.get_location_info(province)
        except Exception as e:
            self.location_error.emit(f"Lỗi khi lấy thông tin vị trí: {str(e)}")
            return {}
            
    def save_location(self, province: str) -> bool:
        """Save location to config"""
        try:
            # Validate province
            if not self.validate_province(province):
                self.location_error.emit("Tỉnh không hợp lệ")
                return False
                
            # Get region
            region = self.get_region_from_province(province)
            if not region:
                self.location_error.emit("Không thể xác định vùng")
                return False
                
            # Get coordinates
            coordinates = self.get_coordinates(province)
            
            # Save to config
            set_setting('location.province', province)
            set_setting('location.region', region)
            set_setting('location.coordinates', coordinates)
            
            # Update current state
            self.current_province = province
            self.current_region = region
            
            # Emit signals
            self.location_changed.emit(province, region)
            self.location_saved.emit()
            
            return True
            
        except Exception as e:
            self.location_error.emit(f"Lỗi khi lưu vị trí: {str(e)}")
            return False
            
    def clear_location(self) -> bool:
        """Clear saved location"""
        try:
            # Clear from config
            set_setting('location.province', None)
            set_setting('location.region', None)
            set_setting('location.coordinates', None)
            
            # Clear current state
            self.current_province = None
            self.current_region = None
            
            # Emit signal with empty values
            self.location_changed.emit("", "")
            
            return True
            
        except Exception as e:
            self.location_error.emit(f"Lỗi khi xóa vị trí: {str(e)}")
            return False
            
    def get_current_location(self) -> Dict[str, Any]:
        """Get current location information"""
        if not self.current_province:
            return {}
            
        return {
            "province": self.current_province,
            "region": self.current_region,
            "coordinates": get_setting('location.coordinates')
        }
