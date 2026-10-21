"""
Prices Page
Shows crop prices in a table/grid layout.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QLineEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QSizePolicy
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont
import re

from controllers.prices_controller import PricesController


class PricesPage(QWidget):
    """Prices page UI shell."""

    def __init__(self):
        super().__init__()
        self.controller = PricesController()
        self.init_ui()
        self.refresh_prices()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Left: filters
        left_panel = QVBoxLayout()
        header = QLabel("Giá cả")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        left_panel.addWidget(header)

        filter_group = QGroupBox("Bộ lọc")
        filter_layout = QVBoxLayout(filter_group)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tìm theo nông sản...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input)

        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Tất cả",
            "Lúa gạo",
            "Cà phê",
            "Hồ tiêu",
            "Cao su",
            "Điều",
            "Rau củ",
            "Trái cây",
        ])
        self.category_combo.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.category_combo)

        self.region_combo = QComboBox()
        self.region_combo.addItems(["Toàn quốc", "Bắc", "Trung", "Nam"])
        self.region_combo.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.region_combo)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Mới nhất",
            "Giá cao → thấp",
            "Giá thấp → cao",
            "Tên A → Z",
        ])
        self.sort_combo.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.sort_combo)

        self.apply_button = QPushButton("Áp dụng")
        self.apply_button.clicked.connect(self.apply_filters)
        filter_layout.addWidget(self.apply_button)

        self.refresh_button = QPushButton("Làm mới")
        self.refresh_button.clicked.connect(self.refresh_prices)
        filter_layout.addWidget(self.refresh_button)

        self.updated_label = QLabel("Cập nhật: --")
        self.updated_label.setStyleSheet("color: #999;")
        filter_layout.addWidget(self.updated_label)

        left_panel.addWidget(filter_group)
        self.detail_box = QGroupBox("Chi tiết")
        detail_layout = QVBoxLayout(self.detail_box)
        self.detail_text = QLabel("Chọn một dòng để xem chi tiết.")
        self.detail_text.setWordWrap(True)
        self.detail_text.setStyleSheet("color: #c0c0c0;")
        detail_layout.addWidget(self.detail_text)
        left_panel.addWidget(self.detail_box)
        left_panel.addStretch()

        # Right: table/grid
        right_panel = QVBoxLayout()
        table_group = QGroupBox("Bảng giá")
        table_layout = QVBoxLayout(table_group)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Nông sản", "Giá", "Đơn vị", "Khu vực", "Cập nhật"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.update_detail_panel)

        table_layout.addWidget(self.table)
        right_panel.addWidget(table_group, 1)

        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 3)

    def refresh_prices(self):
        data = self.controller.get_prices()
        self._all_data = data
        self.updated_label.setText("Cập nhật: " + self._format_last_updated(data.get('last_updated', '')))
        self.apply_filters()

    def apply_filters(self):
        query = self.search_input.text()
        category = self.category_combo.currentText()
        region = self.region_combo.currentText()
        data = self.controller.search_prices(query, category, region)
        items = data.get("items", [])
        items = self._sort_items(items)
        self._populate_table(items)

    def _populate_table(self, items):
        self._current_items = items
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            values = [
                item.get("name", ""),
                item.get("price", ""),
                item.get("unit", ""),
                item.get("region", ""),
                self._format_last_updated(item.get("updated_at", "")),
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))
        if items:
            self.table.setCurrentCell(0, 0)
        else:
            self.detail_text.setText("Chọn một dòng để xem chi tiết.")

    def update_detail_panel(self):
        row = self.table.currentRow()
        if row < 0:
            self.detail_text.setText("Chọn một dòng để xem chi tiết.")
            return
        name = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
        price = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
        unit = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
        region = self.table.item(row, 3).text() if self.table.item(row, 3) else ""
        updated = self.table.item(row, 4).text() if self.table.item(row, 4) else ""
        source = ""
        item = getattr(self, "_current_items", None)
        if item and 0 <= row < len(item):
            source = item[row].get("source", "")
        self.detail_text.setText(
            f"Nông sản: {name}\nGiá: {price} {unit}\nKhu vực: {region}\nCập nhật: {updated}\nNguồn: {source or '--'}"
        )

    def _format_last_updated(self, value: str) -> str:
        if not value:
            return "--"
        for fmt in ("dd/MM/yyyy HH:mm", "dd/MM/yyyy", Qt.ISODate):
            dt = QDateTime.fromString(value, fmt)
            if dt.isValid():
                return dt.toString("dd/MM/yyyy HH:mm")
        return value

    def _parse_price_value(self, price_text: str) -> float:
        if not price_text:
            return 0.0
        cleaned = price_text.replace(",", ".")
        parts = re.split(r"[-–]", cleaned)
        candidate = parts[0].strip() if parts else cleaned
        digits = re.findall(r"\d+(?:\.\d+)?", candidate)
        if not digits:
            return 0.0
        try:
            return float(digits[0])
        except ValueError:
            return 0.0

    def _parse_date_value(self, date_text: str) -> int:
        if not date_text:
            return 0
        for fmt in ("dd/MM/yyyy HH:mm", "dd/MM/yyyy", Qt.ISODate):
            dt = QDateTime.fromString(date_text, fmt)
            if dt.isValid():
                return int(dt.toSecsSinceEpoch())
        return 0

    def _sort_items(self, items):
        mode = self.sort_combo.currentText()
        if mode == "Giá cao → thấp":
            return sorted(items, key=lambda x: self._parse_price_value(x.get("price", "")), reverse=True)
        if mode == "Giá thấp → cao":
            return sorted(items, key=lambda x: self._parse_price_value(x.get("price", "")))
        if mode == "Tên A → Z":
            return sorted(items, key=lambda x: (x.get("name", "") or "").lower())
        return sorted(items, key=lambda x: self._parse_date_value(x.get("updated_at", "")), reverse=True)

    def load_placeholder(self):
        """Optional placeholder rows note for layout testing."""
        self.table.setRowCount(1)
        for col, value in enumerate(["--", "--", "--", "--", "--"]):
            self.table.setItem(0, col, QTableWidgetItem(value))
