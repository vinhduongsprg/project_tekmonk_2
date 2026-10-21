#!/usr/bin/env python3
"""
Farmer Support Desktop Application
Main entry point for the application
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path for supports PyInstaller
if getattr(sys, "frozen", False):
    base_path = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    sys.path.insert(0, str(base_path))
    sys.path.insert(0, str(base_path / "farmer_app"))
else:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from PySide6.QtCore import QTranslator, QLocale
from farmer_app.ui.main_window import MainWindow

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Farmer Support App")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Farmer Support")
    app.setFont(QFont("Segoe UI", 10))
    
    # Initialize and show main window
    window = MainWindow()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
