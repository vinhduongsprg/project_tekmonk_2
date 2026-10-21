"""
Assistant Page
UI shell for the AI assistant feature.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QPushButton,
    QTextEdit,
    QListWidget,
    QComboBox,
    QCheckBox,
    QMessageBox,
    QInputDialog,
)
from PySide6.QtCore import Qt, QObject, Signal, QRunnable, QThreadPool, QTimer
from PySide6.QtGui import QFont, QTextCursor, QTextBlockFormat
import re
from pathlib import Path
import json
from datetime import datetime

from controllers.assistant_controller import AssistantController
from services.connectivity_service import ConnectivityService

class AssistantPage(QWidget):
    """AI assistant page (UI only for now)."""

    def __init__(self):
        super().__init__()
        self.controller = AssistantController()
        self.thread_pool = QThreadPool.globalInstance()
        self.chat_history = []
        self._saved_chats = []
        self._chat_store_path = Path(__file__).resolve().parents[2] / "data" / "chat_history.json"
        self.connectivity_service = ConnectivityService()
        self._online = None
        self.init_ui()
        self._load_saved_chats()
        self._start_connectivity_timer()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Trợ Giúp AI")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(title)

        content_layout = QHBoxLayout()

        left_group = QGroupBox("Lịch sử trò chuyện")
        left_layout = QVBoxLayout(left_group)

        self.history_list = QListWidget()
        self.history_list.itemSelectionChanged.connect(self._on_history_selected)
        self.history_list.setUniformItemSizes(True)
        self.history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_list.setTextElideMode(Qt.ElideRight)
        button_row = QHBoxLayout()
        self.save_chat_button = QPushButton("Lưu đoạn chat")
        self.save_chat_button.clicked.connect(self._save_current_chat)
        self.rename_chat_button = QPushButton("Đổi tên")
        self.rename_chat_button.clicked.connect(self._rename_selected_chat)
        self.exit_chat_button = QPushButton("Thoát đoạn chat")
        self.exit_chat_button.clicked.connect(self._exit_chat_view)
        self.delete_chat_button = QPushButton("Xóa")
        self.delete_chat_button.clicked.connect(self._delete_selected_chat)
        button_row.addWidget(self.save_chat_button)
        button_row.addWidget(self.rename_chat_button)
        button_row.addWidget(self.exit_chat_button)
        button_row.addWidget(self.delete_chat_button)

        left_layout.addWidget(self.history_list, 1)
        left_layout.addLayout(button_row)

        right_group = QGroupBox("Trò chuyện")
        right_layout = QVBoxLayout(right_group)

        mode_layout = QHBoxLayout()
        mode_label = QLabel("Chế độ:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(
            [
                "Ngoại tuyến (dữ liệu nội bộ)",
                "Online AI",
            ]
        )
        self.show_sources_checkbox = QCheckBox("Hiển thị nguồn")
        self.show_sources_checkbox.setChecked(False)
        self.mode_combo.currentIndexChanged.connect(self._update_source_toggle)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addWidget(self.show_sources_checkbox)
        self.connectivity_label = QLabel("Đang kiểm tra...")
        self.connectivity_label.setStyleSheet("color:#9aa0a6; font-size:11px;")
        mode_layout.addWidget(self.connectivity_label)
        mode_layout.addStretch()

        self.chat_view = QTextEdit()
        self.chat_view.setReadOnly(True)
        self.chat_view.setPlaceholderText("Chưa có hội thoại.")

        input_layout = QHBoxLayout()
        self.input_box = QTextEdit()
        self.input_box.setFixedHeight(80)
        self.input_box.setPlaceholderText("Nhập câu hỏi của bạn...")
        self.send_button = QPushButton("Gửi")
        self.clear_button = QPushButton("Xóa")

        input_layout.addWidget(self.input_box, 1)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.clear_button)

        right_layout.addLayout(mode_layout)
        right_layout.addWidget(self.chat_view, 1)
        right_layout.addLayout(input_layout)

        content_layout.addWidget(left_group, 1)
        content_layout.addWidget(right_group, 3)

        layout.addLayout(content_layout, 1)

        self.send_button.clicked.connect(self.on_send_clicked)
        self.clear_button.clicked.connect(self.chat_view.clear)
        self._update_source_toggle()

    def on_send_clicked(self):
        text = self.input_box.toPlainText().strip()
        if not text:
            return
        self._update_connectivity_status()
        if self.mode_combo.currentIndex() == 1 and self._online is False:
            self._append_message("Trợ lý", "Không thể dùng API vì đang ngoại tuyến.")
            return
        self._append_message("Bạn", text)
        self.chat_history.append({"role": "user", "content": text})
        self.input_box.clear()
        self._set_busy(True)
        self._append_message("Trợ lý", "Đang trả lời...")

        prefer_offline = self.mode_combo.currentIndex() == 0
        show_sources = self.show_sources_checkbox.isChecked()
        worker = _AssistantWorker(
            self.controller,
            text,
            list(self.chat_history),
            prefer_offline,
            show_sources,
        )
        worker.signals.finished.connect(self._on_response)
        self.thread_pool.start(worker)

    def _append_message(self, sender: str, message: str, add_separator: bool = False):
        formatted = self._format_message(message)
        html = f"<div style='margin:0;'><b>{sender}:</b> {formatted}</div>"
        cursor = self.chat_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        if cursor.currentList():
            cursor.insertBlock(QTextBlockFormat())
            cursor.createList(0)
        cursor.insertHtml(html)
        cursor.insertBlock()
        if add_separator:
            cursor.insertBlock()

    def _set_busy(self, busy: bool):
        self.send_button.setEnabled(not busy)
        self.input_box.setEnabled(not busy)

    def _on_response(self, response: str, error: str):
        self._set_busy(False)
        if error:
            if error == "missing_api_key":
                self._append_message("Trợ lý", "Thiếu API key. Vui lòng nhập trong Cài Đặt.")
            elif error == "request_failed":
                self._append_message("Trợ lý", "Không thể kết nối tới máy chủ AI.")
            else:
                self._append_message("Trợ lý", "Không nhận được phản hồi hợp lệ.")
            return
        self.chat_history.append({"role": "assistant", "content": response})
        self._append_message("Trợ lý", response, add_separator=True)

    def _update_source_toggle(self):
        offline_mode = self.mode_combo.currentIndex() == 0
        self.show_sources_checkbox.setEnabled(offline_mode)

    def _format_message(self, text: str) -> str:
        if not text:
            return ""
        escaped = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
        escaped = re.sub(r"(?<!\*)\*(.+?)\*(?!\*)", r"<i>\1</i>", escaped)
        lines = escaped.splitlines()
        output = []
        for line in lines:
            if line.strip().startswith("- "):
                output.append(f"• {line.strip()[2:]}")
            else:
                output.append(line if line.strip() else "")
        return "<br>".join(output)

    def _start_connectivity_timer(self):
        self.connectivity_timer = QTimer(self)
        self.connectivity_timer.setInterval(60 * 1000)
        self.connectivity_timer.timeout.connect(self._update_connectivity_status)
        self.connectivity_timer.start()
        self._update_connectivity_status()

    def _update_connectivity_status(self):
        online = self.connectivity_service.is_online()
        self._online = online
        if online:
            self.connectivity_label.setText("Trực tuyến")
        else:
            self.connectivity_label.setText("Ngoại tuyến")

    def _load_saved_chats(self):
        self._saved_chats = []
        if self._chat_store_path.exists():
            try:
                data = json.loads(self._chat_store_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self._saved_chats = data
            except Exception:
                self._saved_chats = []
        self._refresh_history_list()

    def _refresh_history_list(self):
        self.history_list.clear()
        for item in self._saved_chats:
            title = item.get("title", "Đoạn chat")
            created = item.get("created_at", "--/--/---- --:--")
            label = f"{created} - {title}"
            self.history_list.addItem(label)

    def _save_current_chat(self):
        if not self.chat_history:
            QMessageBox.information(self, "Lưu đoạn chat", "Chưa có nội dung để lưu.")
            return
        first_user = next((m for m in self.chat_history if m.get("role") == "user"), None)
        title = (first_user or {}).get("content", "Đoạn chat").strip()
        if len(title) > 40:
            title = title[:37].rstrip() + "..."
        entry = {
            "id": f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": title,
            "created_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "messages": list(self.chat_history),
        }
        self._saved_chats.insert(0, entry)
        self._persist_saved_chats()
        self._refresh_history_list()
        self.history_list.setCurrentRow(0)

    def _persist_saved_chats(self):
        try:
            self._chat_store_path.parent.mkdir(parents=True, exist_ok=True)
            self._chat_store_path.write_text(
                json.dumps(self._saved_chats, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _on_history_selected(self):
        row = self.history_list.currentRow()
        if row < 0 or row >= len(self._saved_chats):
            return
        data = self._saved_chats[row]
        messages = data.get("messages", [])
        self.chat_view.clear()
        self.chat_history = list(messages)
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                self._append_message("Bạn", content)
            elif role == "assistant":
                self._append_message("Trợ lý", content, add_separator=True)

    def _exit_chat_view(self):
        self.history_list.clearSelection()
        self.chat_view.clear()
        self.chat_history = []

    def _delete_selected_chat(self):
        row = self.history_list.currentRow()
        if row < 0 or row >= len(self._saved_chats):
            QMessageBox.information(self, "Xóa đoạn chat", "Chưa chọn đoạn chat.")
            return
        reply = QMessageBox.question(
            self,
            "Xóa đoạn chat",
            "Bạn có chắc muốn xóa đoạn chat này?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._saved_chats.pop(row)
        self._persist_saved_chats()
        self._refresh_history_list()
        self._exit_chat_view()

    def _rename_selected_chat(self):
        row = self.history_list.currentRow()
        if row < 0 or row >= len(self._saved_chats):
            QMessageBox.information(self, "Đổi tên", "Chưa chọn đoạn chat.")
            return
        current = self._saved_chats[row].get("title", "")
        text, ok = QInputDialog.getText(self, "Đổi tên", "Tiêu đề mới:", text=current)
        if not ok:
            return
        new_title = text.strip()
        if not new_title:
            QMessageBox.information(self, "Đổi tên", "Tiêu đề không được để trống.")
            return
        self._saved_chats[row]["title"] = new_title
        self._persist_saved_chats()
        self._refresh_history_list()
        self.history_list.setCurrentRow(row)




class _AssistantWorkerSignals(QObject):
    finished = Signal(str, str)


class _AssistantWorker(QRunnable):
    def __init__(
        self,
        controller: AssistantController,
        text: str,
        history,
        prefer_offline: bool,
        show_sources: bool,
    ):
        super().__init__()
        self.controller = controller
        self.text = text
        self.history = history
        self.prefer_offline = prefer_offline
        self.show_sources = show_sources
        self.signals = _AssistantWorkerSignals()

    def run(self):
        response, error = self.controller.send_message(
            self.text,
            self.history,
            prefer_offline=self.prefer_offline,
            show_sources=self.show_sources,
        )
        self.signals.finished.emit(response or "", error or "")
