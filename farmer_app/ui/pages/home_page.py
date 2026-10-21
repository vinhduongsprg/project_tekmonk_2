"""
Home Page
Main dashboard for the Farmer Support App
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QPushButton
)
from PySide6.QtCore import Qt, QTimer, QDateTime, Signal
from PySide6.QtGui import QFont

from controllers.weather_controller import WeatherController
from controllers.calendar_controller import CalendarController
from config import get_setting


class HomePage(QWidget):
    """Home dashboard page."""

    open_calendar_requested = Signal()

    def __init__(self):
        super().__init__()
        self.weather_controller = WeatherController()
        self.calendar_controller = CalendarController()
        self.init_ui()
        self.refresh_weather()
        self.refresh_today_notes()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Trang Chủ")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(title)

        top_row = QHBoxLayout()

        dashboard_group = QGroupBox("Bảng điều khiển")
        dashboard_layout = QVBoxLayout(dashboard_group)
        dashboard_intro = QLabel("Lịch hôm nay")
        dashboard_intro.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        dashboard_layout.addWidget(dashboard_intro)

        self.today_notes_label = QLabel("Chưa có lịch hôm nay.")
        self.today_notes_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.today_notes_label.setWordWrap(True)
        dashboard_layout.addWidget(self.today_notes_label)

        button_row = QHBoxLayout()
        self.open_calendar_button = QPushButton("Mở lịch")
        self.open_calendar_button.clicked.connect(self.open_calendar_requested.emit)
        self.reload_notes_button = QPushButton("Tải lại")
        self.reload_notes_button.clicked.connect(self.refresh_today_notes)
        button_row.addWidget(self.open_calendar_button)
        button_row.addWidget(self.reload_notes_button)
        button_row.addStretch()
        dashboard_layout.addLayout(button_row)

        weather_group = QGroupBox("Thời tiết")
        weather_layout = QVBoxLayout(weather_group)
        weather_group.setFixedWidth(260)
        self.weather_location = QLabel("Đang tải...")
        self.weather_temp = QLabel("--°C")
        self.weather_condition = QLabel("--")
        self.weather_humidity = QLabel("Độ ẩm: --%")
        self.weather_wind = QLabel("Gió: -- km/h")
        self.weather_precip = QLabel("Lượng mưa: -- mm")
        self.weather_sun = QLabel("Nắng: --")
        self.weather_uv = QLabel("UV: --")
        self.weather_updated = QLabel("Cập nhật: --/--/---- --:--")
        self.weather_updated.setStyleSheet("color: #999; font-size: 10px;")
        self.weather_warning = QLabel("")
        self.weather_warning.setStyleSheet("color: #cc6666; font-size: 10px;")

        self.weather_refresh = QPushButton("Cập nhật")
        self.weather_refresh.clicked.connect(lambda: self.refresh_weather(force=True))

        weather_layout.addWidget(self.weather_location)
        weather_layout.addWidget(self.weather_temp)
        weather_layout.addWidget(self.weather_condition)
        weather_layout.addWidget(self.weather_humidity)
        weather_layout.addWidget(self.weather_wind)
        weather_layout.addWidget(self.weather_precip)
        weather_layout.addWidget(self.weather_sun)
        weather_layout.addWidget(self.weather_uv)
        weather_layout.addWidget(self.weather_updated)
        weather_layout.addWidget(self.weather_warning)

        weather_layout.addWidget(self.weather_refresh)

        interval = int(get_setting("weather.update_interval", 30))
        self.weather_timer = QTimer(self)
        self.weather_timer.setInterval(interval * 60 * 1000)
        self.weather_timer.timeout.connect(self.refresh_weather)
        self.weather_timer.start()

        top_row.addWidget(dashboard_group, 1)
        top_row.addStretch()
        top_row.addWidget(weather_group, 0)

        layout.addLayout(top_row)
        layout.addStretch()

    def refresh_weather(self, force: bool = False):
        data = self.weather_controller.get_current_weather(force=force)
        self._last_weather_data = data
        if data.get("error") == "missing_api_key" and not data.get("current"):
            self.weather_location.setText("Thiếu API key")
            self.weather_temp.setText("--°C")
            self.weather_condition.setText("Cần WEATHERAPI_KEY")
            self.weather_humidity.setText("Độ ẩm: --%")
            self.weather_wind.setText("Gió: -- km/h")
            self.weather_precip.setText("Lượng mưa: -- mm")
            self.weather_sun.setText("Nắng: --")
            self.weather_uv.setText("UV: --")
            self.weather_updated.setText("Cập nhật: --/--/---- --:--")
            self.weather_warning.setText("")
            return
        if data.get("error") and not data.get("current"):
            self.weather_location.setText("Không thể tải")
            self.weather_condition.setText("Lỗi kết nối")
            self.weather_warning.setText("Đang ngoại tuyến (hiển thị dữ liệu cũ)")
            return

        location = data.get("location", {})
        current = data.get("current", {})
        preferred = self.weather_controller.get_default_location()
        name = location.get("name", "Không rõ")
        region = location.get("region", "")
        if preferred:
            display = preferred
        else:
            display = f"{name}" + (f", {region}" if region else "")
        self.weather_location.setText(display)
        self.weather_temp.setText(f"{current.get('temp_c', '--')}°C")
        condition = current.get("condition", {}).get("text", "--")
        self.weather_condition.setText(condition)
        self.weather_humidity.setText(f"Độ ẩm: {current.get('humidity', '--')}%")
        self.weather_wind.setText(f"Gió: {current.get('wind_kph', '--')} km/h")
        self.weather_precip.setText(f"Lượng mưa: {current.get('precip_mm', '--')} mm")
        cloud = current.get("cloud")
        if cloud is None:
            self.weather_sun.setText("Nắng: --")
        else:
            self.weather_sun.setText(f"Nắng: {max(0, 100 - int(cloud))}%")
        self.weather_uv.setText(f"UV: {current.get('uv', '--')}")
        cached_at = data.get("cached_at")
        source = data.get("source", "cache")
        if cached_at:
            ts = QDateTime.fromString(cached_at, Qt.ISODate)
            if ts.isValid():
                display_ts = ts.toString("dd/MM/yyyy HH:mm")
            else:
                display_ts = cached_at
        else:
            display_ts = "--/--/---- --:--"
        suffix = " (cache)" if source == "cache" else " (trực tuyến)"
        self.weather_updated.setText(f"Cập nhật: {display_ts}{suffix}")
        if data.get("error") == "request_failed":
            if data.get("stale", False):
                self.weather_warning.setText("Đang ngoại tuyến (hiển thị dữ liệu cũ)")
            else:
                self.weather_warning.setText("Đang ngoại tuyến")
        else:
            self.weather_warning.setText("")

    def refresh_today_notes(self):
        today = QDateTime.currentDateTime().toString("dd/MM/yyyy")
        entries = self.calendar_controller.get_entries_for_date(today)
        if not entries:
            self.today_notes_label.setText("Chưa có lịch hôm nay.")
            return
        lines = []
        for item in entries[:5]:
            title = item.get("title", "Sự kiện")
            time_text = item.get("time", "")
            prefix = f"{time_text} - " if time_text else ""
            lines.append(f"- {prefix}{title}")
        more = ""
        if len(entries) > 5:
            more = f"\n(+{len(entries) - 5} mục khác)"
        self.today_notes_label.setText("\n".join(lines) + more)

    def set_offline_status(self, offline: bool):
        """Update weather warning based on connectivity."""
        if offline and not self.weather_warning.text():
            stale = False
            data = getattr(self, "_last_weather_data", None)
            if isinstance(data, dict):
                stale = bool(data.get("stale", False))
            self.weather_warning.setText(
                "Đang ngoại tuyến (hiển thị dữ liệu cũ)" if stale else "Đang ngoại tuyến"
            )
        elif not offline and self.weather_warning.text() in (
            "Đang ngoại tuyến (hiển thị dữ liệu cũ)",
            "Đang ngoại tuyến",
        ):
            self.weather_warning.setText("")
