"""
News Page
Shows agricultural news feed (shell).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QListWidget, QListWidgetItem, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtGui import QFont
import html
import re

from controllers.news_controller import NewsController


class NewsPage(QWidget):
    """News page shell."""

    def __init__(self):
        super().__init__()
        self.controller = NewsController()
        self.init_ui()
        self.refresh_news()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Tin Tức")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        self.refresh_button = QPushButton("Cập nhật")
        self.refresh_button.clicked.connect(lambda: self.refresh_news(force=True))
        self.status_label = QLabel("Chưa tải dữ liệu")
        self.status_label.setStyleSheet("color: #999;")
        self.offline_label = QLabel("")
        self.offline_label.setStyleSheet("color: #cc6666;")
        toolbar.addWidget(self.refresh_button)
        toolbar.addWidget(self.status_label)
        toolbar.addWidget(self.offline_label)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        news_group = QGroupBox("Danh sách tin")
        news_layout = QVBoxLayout(news_group)
        news_group.setSizePolicy(news_group.sizePolicy().horizontalPolicy(), QSizePolicy.Expanding)
        self.news_list = QListWidget()
        self.news_list.setUniformItemSizes(True)
        self.news_list.setWordWrap(True)
        self.news_list.setSizePolicy(self.news_list.sizePolicy().horizontalPolicy(), QSizePolicy.Expanding)
        self.news_list.setStyleSheet("""
            QListWidget::item {
                padding: 8px 6px;
                border-bottom: 1px solid #3a3a3a;
            }
        """)
        self.news_list.itemDoubleClicked.connect(self.open_item_link)
        news_layout.addWidget(self.news_list)

        # Placeholder items
        for _ in range(3):
            item = QListWidgetItem("Tiêu đề tin tức\nTóm tắt ngắn sẽ hiển thị ở đây...")
            self.news_list.addItem(item)

        layout.addWidget(news_group, 1)

    def refresh_news(self, force: bool = False):
        data = self.controller.get_news(force=force)
        self._last_news_data = data
        self.news_list.clear()

        if data.get("error") == "no_sources" and not data.get("items"):
            self.status_label.setText("Chưa có nguồn RSS (cài đặt)")
            self.offline_label.setText("")
            return
        if data.get("error") and not data.get("items"):
            self.status_label.setText("Không thể tải tin")
            self.offline_label.setText("Đang ngoại tuyến (hiển thị dữ liệu cũ)")
            return

        items = data.get("items", [])
        if not items:
            self.status_label.setText("Không có tin mới")
            return

        source = data.get("source", "cache")
        self.status_label.setText("Dữ liệu cache" if source == "cache" else "Đã cập nhật")
        if data.get("error") == "request_failed":
            if data.get("stale", False):
                self.offline_label.setText("Đang ngoại tuyến (hiển thị dữ liệu cũ)")
            else:
                self.offline_label.setText("Đang ngoại tuyến")
        else:
            self.offline_label.setText("")

        for item in items:
            title = item.get("title", "")
            summary = item.get("summary", "")
            summary = self._clean_summary(summary)
            published = item.get("published", "")
            source_name = item.get("source", "")
            list_item = QListWidgetItem()
            list_item.setData(Qt.UserRole, item.get("link", ""))
            widget = self._create_news_item_widget(title, summary, published, source_name)
            list_item.setSizeHint(widget.sizeHint())
            self.news_list.addItem(list_item)
            self.news_list.setItemWidget(list_item, widget)

        # No animation (kept simple for performance and clarity).

    def _clean_summary(self, summary: str) -> str:
        if not summary:
            return ""
        # Strip HTML tags and decode entities.
        clean = re.sub(r"<[^>]+>", " ", summary)
        clean = html.unescape(clean)
        clean = " ".join(clean.split())
        # Keep it short for the list view.
        return clean[:140] + ("..." if len(clean) > 140 else "")

    def _create_news_item_widget(self, title: str, summary: str, published: str, source_name: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        title_label = QLabel(title)
        title_font = QFont("Arial", 10, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setWordWrap(True)

        meta_parts = []
        if source_name:
            meta_parts.append(source_name)
        if published:
            meta_parts.append(published)
        meta_text = " • ".join(meta_parts)
        meta_label = QLabel(meta_text)
        meta_label.setStyleSheet("color: #999; font-size: 10px;")
        meta_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

        header.addWidget(title_label, 1)
        header.addWidget(meta_label, 0)
        layout.addLayout(header)

        if summary:
            summary_label = QLabel(summary)
            summary_label.setWordWrap(True)
            summary_label.setStyleSheet("color: #c0c0c0;")
            layout.addWidget(summary_label)

        return widget

    def set_offline_status(self, offline: bool):
        if offline and not self.offline_label.text():
            stale = False
            data = getattr(self, "_last_news_data", None)
            if isinstance(data, dict):
                stale = bool(data.get("stale", False))
            self.offline_label.setText(
                "Đang ngoại tuyến (hiển thị dữ liệu cũ)" if stale else "Đang ngoại tuyến"
            )
        elif not offline and self.offline_label.text() in (
            "Đang ngoại tuyến (hiển thị dữ liệu cũ)",
            "Đang ngoại tuyến",
        ):
            self.offline_label.setText("")

    def open_item_link(self, item: QListWidgetItem):
        link = item.data(Qt.UserRole)
        if link:
            QDesktopServices.openUrl(QUrl(link))
