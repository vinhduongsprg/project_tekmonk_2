"""
Main Application Window
Contains navigation and page management for the Farmer Support App
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QStatusBar, QLabel, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QDateTime
from PySide6.QtGui import QIcon

from config import get_setting, set_setting
from .pages.home_page import HomePage
from .pages.location_page import LocationPage
from .pages.news_page import NewsPage
from .pages.prices_page import PricesPage
from .pages.calendar_page import CalendarPage
from .pages.settings_page import SettingsPage
from .pages.notes_page import NotesPage
from .pages.assistant_page import AssistantPage
from services.connectivity_service import ConnectivityService


class MainWindow(QMainWindow):
    """Main application window with navigation"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hỗ Trợ Nông Dân")
        self.setMinimumSize(1000, 700)

        # Initialize UI components
        self.init_ui()
        self.setup_status_bar()
        self.setup_navigation()
        self.setup_connectivity()
        self.load_settings()

    def init_ui(self):
        """Initialize the main UI layout"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Navigation sidebar
        self.nav_widget = QWidget()
        self.nav_widget.setMaximumWidth(200)
        self.nav_layout = QVBoxLayout(self.nav_widget)

        # Divider between nav and content
        self.nav_divider = QFrame()
        self.nav_divider.setFrameShape(QFrame.VLine)
        self.nav_divider.setFrameShadow(QFrame.Plain)
        self.nav_divider.setStyleSheet("color: #3a3a3a;")

        # Page stack
        self.page_stack = QStackedWidget()

        # Add to main layout
        main_layout.addWidget(self.nav_widget)
        main_layout.addWidget(self.nav_divider)
        main_layout.addWidget(self.page_stack, 1)

    def setup_navigation(self):
        """Setup navigation buttons"""
        # Navigation buttons (Vietnamese labels)
        self.nav_buttons = {
            "home": self.create_nav_button("Trang Chủ", "home"),
            "location": self.create_nav_button("Vị Trí", "location"),
            "news": self.create_nav_button("Tin Tức", "news"),
            "prices": self.create_nav_button("Giá Cả", "prices"),
            "calendar": self.create_nav_button("Lịch", "calendar"),
            "notes": self.create_nav_button("Ghi Chú", "notes"),
            "assistant": self.create_nav_button("Trợ Giúp AI", "assistant"),
            "settings": self.create_nav_button("Cài Đặt", "settings"),
        }

        # Add buttons to navigation layout
        for button in self.nav_buttons.values():
            self.nav_layout.addWidget(button)

        # Add stretch to push buttons to top
        self.nav_layout.addStretch()

        # Connect button signals
        for page_name, button in self.nav_buttons.items():
            button.clicked.connect(lambda checked, name=page_name: self.navigate_to_page(name))

        # Create placeholder pages
        self.create_placeholder_pages()

        # Navigate to home page by default
        self.navigate_to_page("home")

    def create_nav_button(self, text, page_name):
        """Create a navigation button"""
        button = QPushButton(text)
        button.setMinimumHeight(40)
        button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 10px;
                border: 1px solid transparent;
                background-color: transparent;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
            }
            QPushButton:pressed {
                background-color: #1f1f1f;
            }
        """)
        return button

    def create_placeholder_pages(self):
        """Create pages for each section"""
        # Create actual pages
        self.home_page = HomePage()
        self.location_page = LocationPage()
        self.news_page = NewsPage()
        self.prices_page = PricesPage()
        self.calendar_page = CalendarPage()
        self.notes_page = NotesPage()
        self.assistant_page = AssistantPage()
        self.settings_page = SettingsPage()
        self.settings_page.connectivity_check_requested.connect(self.update_connectivity_status)
        self.location_page.location_changed.connect(self.on_location_changed)
        self.calendar_page.entry_selected.connect(self.on_calendar_entry_selected)
        self.notes_page.open_in_calendar_requested.connect(self.on_note_open_in_calendar)
        self.home_page.open_calendar_requested.connect(self._open_calendar_from_home)

        # Create placeholder pages for other sections
        pages = [
            ("Trang Chủ", "home", self.home_page),
            ("Vị Trí", "location", self.location_page),
            ("Tin Tức", "news", self.news_page),
            ("Giá Cả", "prices", self.prices_page),
            ("Lịch", "calendar", self.calendar_page),
            ("Ghi Chú", "notes", self.notes_page),
            ("Trợ Giúp AI", "assistant", self.assistant_page),
            ("Cài Đặt", "settings", self.settings_page),
        ]

        for title, page_name, custom_page in pages:
            if custom_page:
                page = custom_page
            else:
                page = QWidget()
                layout = QVBoxLayout(page)

                label = QLabel(f"{title}\n\n(Đang phát triển...)")
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("""
                    QLabel {
                        font-size: 18px;
                        color: #666;
                        padding: 50px;
                    }
                """)

                layout.addWidget(label)

            self.page_stack.addWidget(page)

    def navigate_to_page(self, page_name):
        """Navigate to a specific page"""
        page_indices = {
            "home": 0,
            "location": 1,
            "news": 2,
            "prices": 3,
            "calendar": 4,
            "notes": 5,
            "assistant": 6,
            "settings": 7,
        }

        if page_name in page_indices:
            self.page_stack.setCurrentIndex(page_indices[page_name])
            self.update_status_page(page_name)
            if page_name == "notes":
                self.notes_page.refresh_notes()
            if page_name == "home":
                self.home_page.refresh_today_notes()

            # Update button styles
            for name, button in self.nav_buttons.items():
                if name == page_name:
                    button.setStyleSheet("""
                        QPushButton {
                            text-align: left;
                            padding-left: 10px;
                            border: 1px solid transparent;
                            background-color: #2a5dff;
                            color: white;
                            border-radius: 6px;
                        }
                    """)
                else:
                    button.setStyleSheet("""
                        QPushButton {
                            text-align: left;
                            padding-left: 10px;
                            border: 1px solid transparent;
                            background-color: transparent;
                            border-radius: 6px;
                        }
                        QPushButton:hover {
                            background-color: #2a2a2a;
                        }
                    """)

    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #1e1e1e;
                color: #e6e6e6;
                border-top: 1px solid #3a3a3a;
            }
            QStatusBar QLabel {
                padding: 0 10px;
                border-right: 1px solid #3a3a3a;
            }
            QStatusBar QLabel:last-child {
                border-right: none;
            }
        """)

        # Page label (left)
        self.page_label = QLabel("Đang ở: Trang Chủ")
        self.status_bar.addWidget(self.page_label, 1)

        # Connection status label
        self.connection_label = _ClickableLabel("🔴 Ngoại tuyến")
        self.connection_label.clicked.connect(self.on_connectivity_label_clicked)
        self.status_bar.addPermanentWidget(self.connection_label)

        self.connectivity_time_label = QLabel("")
        self.status_bar.addPermanentWidget(self.connectivity_time_label)

        # Location label
        self.location_label = QLabel("Chưa chọn vị trí")
        self.status_bar.addPermanentWidget(self.location_label)

    def update_status_page(self, page_name):
        """Update status bar page label"""
        page_names = {
            "home": "Trang Chủ",
            "location": "Vị Trí",
            "news": "Tin Tức",
            "prices": "Giá Cả",
            "calendar": "Lịch",
            "notes": "Ghi Chú",
            "assistant": "Trợ Giúp AI",
            "settings": "Cài Đặt",
        }
        label = page_names.get(page_name, page_name)
        self.page_label.setText(f"Đang ở: {label}")

    def on_location_changed(self, province, region):
        """Handle location change"""
        if province and region:
            self.location_label.setText(f"{province} ({region})")
        else:
            self.location_label.setText("Chưa chọn vị trí")

    def on_calendar_entry_selected(self, entry: dict):
        note_id = entry.get("note_id")
        if not note_id:
            return
        self.notes_page.select_note_by_id(note_id)
        self.navigate_to_page("notes")

    def on_note_open_in_calendar(self, date_str: str):
        self.calendar_page.jump_to_date(date_str)
        self.navigate_to_page("calendar")

    def _open_calendar_from_home(self):
        self.navigate_to_page("calendar")

    def load_settings(self):
        """Load application settings"""
        # Load window size and position
        window_size = get_setting("ui.window_size", [1000, 700])
        window_position = get_setting("ui.window_position", [100, 100])

        self.resize(window_size[0], window_size[1])
        self.move(window_position[0], window_position[1])

        # Load location
        province = get_setting("location.province")
        region = get_setting("location.region")
        if province and region:
            self.location_label.setText(f"{province} ({region})")

        # Load last update timestamp for connectivity label.
        last_update = get_setting("app.last_update")
        if last_update:
            ts = QDateTime.fromString(last_update, Qt.ISODate)
            if ts.isValid():
                self._last_online = ts

    def setup_connectivity(self):
        """Setup periodic connectivity checks."""
        self.connectivity_service = ConnectivityService()
        self._last_online = None
        self._last_checked = None
        self.connectivity_timer = QTimer(self)
        interval = get_setting("connectivity.check_interval", 5)
        self.connectivity_timer.setInterval(int(interval) * 60 * 1000)
        self.connectivity_timer.timeout.connect(self.update_connectivity_status)
        self.connectivity_timer.start()
        self.update_connectivity_status()

    def update_connectivity_status(self):
        online = self.connectivity_service.is_online()
        self._last_checked = QDateTime.currentDateTime()
        if online:
            self.connection_label.setText("🟢 Trực tuyến")
            self._last_online = self._last_checked
            set_setting("app.last_update", self._last_checked.toString(Qt.ISODate))
        else:
            self.connection_label.setText("🔴 Ngoại tuyến")
        self._update_connectivity_time_label(online)
        self._handle_connectivity_refresh(online)
        if hasattr(self, "home_page"):
            self.home_page.set_offline_status(not online)
        if hasattr(self, "news_page"):
            self.news_page.set_offline_status(not online)

    def _update_connectivity_time_label(self, online: bool):
        label = "Lần cuối cập nhật:"
        if online:
            if self._last_checked:
                ts = self._last_checked.toString("dd/MM/yyyy HH:mm")
                self.connectivity_time_label.setText(f"{label} {ts}")
        else:
            if self._last_online:
                ts = self._last_online.toString("dd/MM/yyyy HH:mm")
                self.connectivity_time_label.setText(f"{label} {ts}")
            else:
                self.connectivity_time_label.setText(f"{label} --/--/---- --:--")

    def _handle_connectivity_refresh(self, online: bool):
        if online and hasattr(self, "_was_online"):
            if not self._was_online and hasattr(self, "home_page"):
                self.home_page.refresh_weather()
        self._was_online = online

    def on_connectivity_label_clicked(self):
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Kết nối")
        dialog.setText(f"Trạng thái: {self.connection_label.text()}")
        check_button = dialog.addButton("Kiểm tra ngay", QMessageBox.ActionRole)
        dialog.addButton("Đóng", QMessageBox.RejectRole)

        def _do_check():
            self.update_connectivity_status()
            dialog.setText(f"Trạng thái: {self.connection_label.text()}")

        check_button.clicked.connect(_do_check)
        dialog.exec()

    def closeEvent(self, event):
        """Save settings when closing the application"""
        # Save window size and position
        set_setting("ui.window_size", [self.width(), self.height()])
        set_setting("ui.window_position", [self.x(), self.y()])

        event.accept()


class _ClickableLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
