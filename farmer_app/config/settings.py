"""
Configuration Management for Farmer Support App
Handles application settings and user preferences
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class SettingsManager:
    """Manages application configuration and settings"""
    
    def __init__(self):
        # Get data directory (create if doesn't exist)
        self.data_dir = Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # Config file path
        self.config_file = self.data_dir / "config.json"
        
        # Default configuration
        self.default_config = {
            "location": {
                "province": None,
                "region": None,
                "coordinates": None
            },
            "weather": {
                "api_key": None,
                "update_interval": 30,  # minutes
                "units": "metric"
            },
            "connectivity": {
                "check_interval": 5  # minutes
            },
            "news": {
                "update_interval": 6,  # hours
                "sources": []
            },
            "ai": {
                "api_key": None,
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4o-mini",
                "temperature": 0.3,
                "system_prompt": "Bạn là trợ lý nông nghiệp. Trả lời ngắn gọn, rõ ràng, ưu tiên an toàn.",
                "preset": "custom"
            },
            "ui": {
                "language": "vi",
                "theme": "light",
                "window_size": [1000, 700],
                "window_position": [100, 100]
            },
            "calendar": {
                "first_day_of_week": 1,  # Monday
                "time_format": "24h"
            },
            "app": {
                "version": "1.0.0",
                "first_run": True,
                "last_update": None
            }
        }
        
        # Load existing config or create default
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge with defaults to handle missing keys
                config = self.default_config.copy()
                self._deep_update(config, loaded_config)
                return config
                
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}")
                return self.default_config.copy()
        else:
            # Create default config file
            self.save_config(self.default_config)
            return self.default_config.copy()
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Save configuration to file"""
        if config is None:
            config = self.config
            
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'location.province')"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        return self.save_config()
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to default values"""
        self.config = self.default_config.copy()
        return self.save_config()
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """Recursively update dictionary"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value


# Global settings instance
settings = SettingsManager()


# Convenience functions
def get_setting(key: str, default: Any = None) -> Any:
    """Get setting value"""
    return settings.get(key, default)


def set_setting(key: str, value: Any) -> bool:
    """Set setting value"""
    return settings.set(key, value)


def save_settings() -> bool:
    """Save current settings"""
    return settings.save_config()
