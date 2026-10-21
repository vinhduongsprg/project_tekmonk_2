"""
Settings Page
Lightweight settings for API keys and preferences.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QGroupBox,
    QHBoxLayout, QPushButton, QComboBox, QSpinBox, QMessageBox, QTextEdit,
    QCheckBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from pathlib import Path
import json

from config import get_setting, set_setting


class SettingsPage(QWidget):
    """Light settings page."""

    connectivity_check_requested = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Cài Đặt")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(title)

        weather_group = QGroupBox("Thời tiết")
        weather_layout = QVBoxLayout(weather_group)

        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("WeatherAPI key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Nhập API key")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        key_row.addWidget(self.api_key_input, 1)
        self.show_key_checkbox = QCheckBox("Hiện API key")
        self.show_key_checkbox.toggled.connect(self.toggle_api_key_visibility)
        key_row.addWidget(self.show_key_checkbox)

        interval_row = QHBoxLayout()
        interval_row.addWidget(QLabel("Cập nhật (phút):"))
        self.update_interval = QSpinBox()
        self.update_interval.setRange(5, 180)
        interval_row.addWidget(self.update_interval)

        units_row = QHBoxLayout()
        units_row.addWidget(QLabel("Đơn vị:"))
        self.units_combo = QComboBox()
        self.units_combo.addItems(["metric", "imperial"])
        units_row.addWidget(self.units_combo)

        weather_layout.addLayout(key_row)
        weather_layout.addLayout(interval_row)
        weather_layout.addLayout(units_row)

        connectivity_group = QGroupBox("Kết nối")
        connectivity_layout = QVBoxLayout(connectivity_group)
        conn_row = QHBoxLayout()
        conn_row.addWidget(QLabel("Kiểm tra (phút):"))
        self.connectivity_interval = QSpinBox()
        self.connectivity_interval.setRange(1, 60)
        conn_row.addWidget(self.connectivity_interval)
        connectivity_layout.addLayout(conn_row)

        self.connectivity_check_button = QPushButton("Kiểm tra ngay")
        self.connectivity_check_button.clicked.connect(self.connectivity_check_requested.emit)
        connectivity_layout.addWidget(self.connectivity_check_button)

        news_group = QGroupBox("Tin tức")
        news_layout = QVBoxLayout(news_group)

        news_interval_row = QHBoxLayout()
        news_interval_row.addWidget(QLabel("Cập nhật (giờ):"))
        self.news_update_interval = QSpinBox()
        self.news_update_interval.setRange(1, 24)
        news_interval_row.addWidget(self.news_update_interval)

        news_sources_label = QLabel("Nguồn RSS (mỗi dòng một URL):")
        self.news_sources_input = QTextEdit()
        self.news_sources_input.setPlaceholderText("https://example.com/rss")
        self.news_sources_input.setFixedHeight(100)

        news_layout.addLayout(news_interval_row)
        news_layout.addWidget(news_sources_label)
        news_layout.addWidget(self.news_sources_input)

        ai_group = QGroupBox("Trợ giúp AI")
        ai_layout = QVBoxLayout(ai_group)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Preset:"))
        self.ai_preset_combo = QComboBox()
        preset_row.addWidget(self.ai_preset_combo)

        ai_key_row = QHBoxLayout()
        ai_key_row.addWidget(QLabel("API key:"))
        self.ai_key_input = QLineEdit()
        self.ai_key_input.setPlaceholderText("Nhập API key")
        self.ai_key_input.setEchoMode(QLineEdit.Password)
        ai_key_row.addWidget(self.ai_key_input, 1)
        self.ai_show_key_checkbox = QCheckBox("Hiện API key")
        self.ai_show_key_checkbox.toggled.connect(self.toggle_ai_key_visibility)
        ai_key_row.addWidget(self.ai_show_key_checkbox)

        ai_model_row = QHBoxLayout()
        ai_model_row.addWidget(QLabel("Model:"))
        self.ai_model_combo = QComboBox()
        self.ai_model_combo.setEditable(True)
        self.ai_model_combo.addItems([
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4.1-mini",
            "gpt-4.1",
        ])
        self.ai_model_combo.setEditText("gpt-4o-mini")
        ai_model_row.addWidget(self.ai_model_combo)

        ai_url_row = QHBoxLayout()
        ai_url_row.addWidget(QLabel("Base URL:"))
        self.ai_base_url_input = QLineEdit()
        self.ai_base_url_input.setPlaceholderText("https://api.openai.com/v1")
        ai_url_row.addWidget(self.ai_base_url_input)

        ai_temp_row = QHBoxLayout()
        ai_temp_row.addWidget(QLabel("Nhiệt độ:"))
        self.ai_temperature = QDoubleSpinBox()
        self.ai_temperature.setRange(0.0, 2.0)
        self.ai_temperature.setSingleStep(0.1)
        ai_temp_row.addWidget(self.ai_temperature)

        self.ai_model_combo.currentTextChanged.connect(self._update_ai_warning)
        self.ai_base_url_input.textChanged.connect(self._update_ai_warning)

        self.ai_warning = QLabel("")
        self.ai_warning.setStyleSheet("color: #cc6666; font-size: 11px;")
        self.ai_test_button = QPushButton("Kiểm tra API")
        self.ai_test_button.clicked.connect(self.test_ai_connection)

        ai_layout.addLayout(preset_row)
        ai_layout.addLayout(ai_key_row)
        ai_layout.addLayout(ai_model_row)
        ai_layout.addLayout(ai_url_row)
        ai_layout.addLayout(ai_temp_row)
        ai_layout.addWidget(self.ai_warning)
        ai_layout.addWidget(self.ai_test_button)

        button_row = QHBoxLayout()
        self.save_button = QPushButton("Lưu")
        self.save_button.clicked.connect(self.save_settings)
        button_row.addWidget(self.save_button)
        button_row.addStretch()

        layout.addWidget(weather_group)
        layout.addWidget(connectivity_group)
        layout.addWidget(news_group)
        layout.addWidget(ai_group)
        layout.addLayout(button_row)
        layout.addStretch()

    def load_settings(self):
        self.api_key_input.setText(get_setting("weather.api_key") or "")
        self.update_interval.setValue(int(get_setting("weather.update_interval", 30)))
        self.units_combo.setCurrentText(get_setting("weather.units", "metric"))
        self.connectivity_interval.setValue(int(get_setting("connectivity.check_interval", 5)))
        self.news_update_interval.setValue(int(get_setting("news.update_interval", 6)))
        sources = get_setting("news.sources", [])
        if isinstance(sources, list):
            self.news_sources_input.setPlainText("\n".join(sources))
        self.ai_key_input.setText(get_setting("ai.api_key") or "")
        self._load_ai_presets()
        preset_id = get_setting("ai.preset", "custom")
        self._set_preset_by_id(preset_id)
        self.ai_model_combo.setCurrentText(get_setting("ai.model", "gpt-4o-mini"))
        self.ai_base_url_input.setText(get_setting("ai.base_url", "https://api.openai.com/v1"))
        self.ai_temperature.setValue(float(get_setting("ai.temperature", 0.3)))
        self._update_ai_warning()

    def save_settings(self):
        api_key = self.api_key_input.text().strip()
        interval = self.update_interval.value()
        units = self.units_combo.currentText()

        set_setting("weather.api_key", api_key or None)
        set_setting("weather.update_interval", interval)
        set_setting("weather.units", units)
        set_setting("connectivity.check_interval", self.connectivity_interval.value())
        sources_text = self.news_sources_input.toPlainText().splitlines()
        sources = [s.strip() for s in sources_text if s.strip()]
        set_setting("news.update_interval", self.news_update_interval.value())
        set_setting("news.sources", sources)
        set_setting("ai.api_key", self.ai_key_input.text().strip() or None)
        set_setting("ai.model", self.ai_model_combo.currentText().strip() or "gpt-4o-mini")
        set_setting("ai.base_url", self.ai_base_url_input.text().strip() or "https://api.openai.com/v1")
        set_setting("ai.temperature", float(self.ai_temperature.value()))
        preset_id = self.ai_preset_combo.currentData()
        set_setting("ai.preset", preset_id or "custom")

        QMessageBox.information(self, "Cài Đặt", "Đã lưu Cài Đặt.")

    def toggle_api_key_visibility(self, checked: bool):
        self.api_key_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    def toggle_ai_key_visibility(self, checked: bool):
        self.ai_key_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    def _load_ai_presets(self):
        self.ai_preset_combo.clear()
        presets = self._read_ai_presets()
        for preset in presets:
            self.ai_preset_combo.addItem(preset.get("label", preset.get("id", "Custom")), preset)
        self.ai_preset_combo.currentIndexChanged.connect(self._apply_selected_preset)

    def _read_ai_presets(self):
        preset_path = Path(__file__).resolve().parents[2] / "data" / "ai_models.json"
        if not preset_path.exists():
            return [{"id": "custom", "label": "Custom"}]
        try:
            return json.loads(preset_path.read_text(encoding="utf-8"))
        except Exception:
            return [{"id": "custom", "label": "Custom"}]

    def _set_preset_by_id(self, preset_id: str):
        for index in range(self.ai_preset_combo.count()):
            preset = self.ai_preset_combo.itemData(index)
            if preset and preset.get("id") == preset_id:
                self.ai_preset_combo.setCurrentIndex(index)
                return

    def _apply_selected_preset(self):
        preset = self.ai_preset_combo.currentData()
        if not preset:
            return
        base_url = preset.get("base_url")
        model = preset.get("model")
        temperature = preset.get("temperature")
        if base_url:
            self.ai_base_url_input.setText(base_url)
        if model:
            self.ai_model_combo.setCurrentText(model)
        if isinstance(temperature, (int, float)):
            self.ai_temperature.setValue(float(temperature))
        self._update_ai_warning()

    def _update_ai_warning(self):
        model = self.ai_model_combo.currentText().strip().lower()
        base_url = self.ai_base_url_input.text().strip().lower()
        if model and "deepseek" in model and "openai" in base_url:
            self.ai_warning.setText("Model đang là DeepSeek nhưng Base URL là OpenAI. Hãy đổi Base URL đúng.")
        else:
            self.ai_warning.setText("")

    def test_ai_connection(self):
        api_key = self.ai_key_input.text().strip()
        base_url = self.ai_base_url_input.text().strip()
        model = self.ai_model_combo.currentText().strip()
        if not api_key:
            QMessageBox.warning(self, "Kiểm tra API", "Thiếu API key.")
            return
        if not base_url or not model:
            QMessageBox.warning(self, "Kiểm tra API", "Thiếu Base URL hoặc Model.")
            return

        import requests
        url = base_url.rstrip("/")
        is_gemini = "generativelanguage.googleapis.com" in base_url.lower() or model.lower().startswith("gemini")
        if is_gemini:
            endpoint = f"{url}/v1beta/models/{model}:generateContent"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": "ping"}]}],
                "generationConfig": {"temperature": 0},
            }
            headers = {"Content-Type": "application/json"}
            params = {"key": api_key}
        else:
            if url.endswith("/v1"):
                endpoint = f"{url}/chat/completions"
            elif "/v1" in url:
                endpoint = f"{url}/chat/completions"
            else:
                endpoint = f"{url}/v1/chat/completions"
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "ping"}],
                "temperature": 0,
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            params = None
        try:
            resp = requests.post(endpoint, params=params, json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                QMessageBox.information(self, "Kiểm tra API", "Kết nối thành công.")
            else:
                QMessageBox.warning(
                    self,
                    "Kiểm tra API",
                    f"Lỗi {resp.status_code}:\n{resp.text[:500]}",
                )
        except requests.RequestException as exc:
            QMessageBox.warning(self, "Kiểm tra API", f"Lỗi kết nối:\n{exc}")
