"""
Configuration Package for Farmer Support App
"""

from .settings import SettingsManager, settings, get_setting, set_setting, save_settings

__all__ = ['SettingsManager', 'settings', 'get_setting', 'set_setting', 'save_settings']
