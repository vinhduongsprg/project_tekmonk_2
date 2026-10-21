"""
Notes Page
List of notes on the left, editor on the right.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QListWidget, QListWidgetItem, QPushButton, QLineEdit,
    QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QDateTime, QDate, Signal
from PySide6.QtGui import QFont

from controllers.notes_controller import NotesController
from services.notes_service import NotesService


class NotesPage(QWidget):
    """Notes page UI."""

    open_in_calendar_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.controller = NotesController()
        self.service = self.controller.service
        self._selected_note_id = None
        self._last_snapshot = None
        self.init_ui()
        self.refresh_notes()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Left: list + search
        left_panel = QVBoxLayout()
        left_title = QLabel("Ghi chú")
        left_title.setFont(QFont("Arial", 14, QFont.Bold))
        left_panel.addWidget(left_title)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tìm kiếm...")
        self.search_input.textChanged.connect(self.on_search)
        left_panel.addWidget(self.search_input)

        self.notes_list = QListWidget()
        self.notes_list.itemSelectionChanged.connect(self.on_note_selected)
        left_panel.addWidget(self.notes_list, 1)

        self.new_button = QPushButton("Ghi chú mới")
        self.new_button.clicked.connect(self.new_note)
        left_panel.addWidget(self.new_button)

        # Right: editor
        right_panel = QVBoxLayout()
        header = QLabel("Soạn thảo")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        right_panel.addWidget(header)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Tiêu đề")
        right_panel.addWidget(self.title_input)

        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("Ngày liên kết (dd/MM/yyyy)")
        right_panel.addWidget(self.date_input)

        self.content_input = QTextEdit()
        right_panel.addWidget(self.content_input, 1)

        meta_row = QHBoxLayout()
        self.created_label = QLabel("Ngày tạo: --")
        self.updated_label = QLabel("Chỉnh sửa: --")
        meta_row.addWidget(self.created_label)
        meta_row.addStretch()
        meta_row.addWidget(self.updated_label)
        right_panel.addLayout(meta_row)

        button_row = QHBoxLayout()
        self.save_button = QPushButton("Lưu")
        self.delete_button = QPushButton("Xóa")
        self.redo_button = QPushButton("Hoàn tác")
        self.open_calendar_button = QPushButton("Mở trong lịch")
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.redo_button)
        button_row.addWidget(self.delete_button)
        button_row.addWidget(self.open_calendar_button)
        right_panel.addLayout(button_row)

        self.save_button.clicked.connect(self.save_note)
        self.delete_button.clicked.connect(self.delete_note)
        self.redo_button.clicked.connect(self.redo_note)
        self.open_calendar_button.clicked.connect(self.open_in_calendar)

        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 2)

    def refresh_notes(self):
        self.notes_list.clear()
        notes = self.controller.get_all_notes()
        for note in notes:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, note)
            widget = self._create_note_item_widget(note)
            item.setSizeHint(widget.sizeHint())
            self.notes_list.addItem(item)
            self.notes_list.setItemWidget(item, widget)

    def on_search(self, text: str):
        self.notes_list.clear()
        notes = self.controller.search_notes(text)
        for note in notes:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, note)
            widget = self._create_note_item_widget(note)
            item.setSizeHint(widget.sizeHint())
            self.notes_list.addItem(item)
            self.notes_list.setItemWidget(item, widget)

    def on_note_selected(self):
        items = self.notes_list.selectedItems()
        if not items:
            return
        note = items[0].data(Qt.UserRole) or {}
        self._selected_note_id = note.get("id")
        self._last_snapshot = note.copy()
        self.title_input.setText(note.get("title", ""))
        self.date_input.setText(note.get("linked_date", ""))
        self.content_input.setPlainText(note.get("content", ""))
        self.created_label.setText(f"Ngày tạo: {note.get('created_at', '--')}")
        self.updated_label.setText(f"Chỉnh sửa: {note.get('updated_at', '--')}")
        self.open_calendar_button.setEnabled(bool(note.get("linked_date")))

    def new_note(self):
        self._selected_note_id = None
        self._last_snapshot = None
        self.title_input.setText("Ghi chú mới")
        self.date_input.setText("")
        self.content_input.setPlainText("")
        self.created_label.setText("Ngày tạo: --")
        self.updated_label.setText("Chỉnh sửa: --")
        self.open_calendar_button.setEnabled(False)

    def save_note(self):
        now = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss")
        linked_date = self.date_input.text().strip()
        if linked_date and not QDate.fromString(linked_date, "dd/MM/yyyy").isValid():
            QMessageBox.warning(self, "Ngày", "Ngày liên kết không hợp lệ.")
            return
        note = {
            "id": self._selected_note_id or self.service.generate_id("note"),
            "title": self.title_input.text().strip() or "Không tiêu đề",
            "linked_date": linked_date,
            "content": self.content_input.toPlainText().strip(),
            "created_at": self._last_snapshot.get("created_at") if self._last_snapshot else now,
            "updated_at": now,
        }
        if self._selected_note_id:
            self.controller.update_note(note)
        else:
            self.controller.add_note(note)
        self.refresh_notes()
        self.updated_label.setText(f"Chỉnh sửa: {note.get('updated_at')}")
        self.created_label.setText(f"Ngày tạo: {note.get('created_at')}")
        self._selected_note_id = note["id"]
        self.open_calendar_button.setEnabled(bool(note.get("linked_date")))

    def delete_note(self):
        if not self._selected_note_id:
            return
        confirm = QMessageBox.question(
            self,
            "Xóa ghi chú",
            "Bạn có chắc muốn xóa ghi chú này?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        self.controller.delete_note(self._selected_note_id)
        self.new_note()
        self.refresh_notes()

    def redo_note(self):
        snapshot = self._last_snapshot
        if not snapshot:
            return
        self.title_input.setText(snapshot.get("title", ""))
        self.date_input.setText(snapshot.get("linked_date", ""))
        self.content_input.setPlainText(snapshot.get("content", ""))
        self.created_label.setText(f"Ngày tạo: {snapshot.get('created_at', '--')}")
        self.updated_label.setText(f"Chỉnh sửa: {snapshot.get('updated_at', '--')}")
        self.open_calendar_button.setEnabled(bool(snapshot.get("linked_date")))

    def open_in_calendar(self):
        linked_date = self.date_input.text().strip()
        if linked_date:
            self.open_in_calendar_requested.emit(linked_date)

    def select_note_by_id(self, note_id: str):
        for i in range(self.notes_list.count()):
            item = self.notes_list.item(i)
            data = item.data(Qt.UserRole) or {}
            if data.get("id") == note_id:
                self.notes_list.setCurrentItem(item)
                break

    def _create_note_item_widget(self, note: dict) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        title = note.get("title", "Không tiêu đề")
        left = QLabel(title)
        left.setWordWrap(True)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(2)

        linked_date = note.get("linked_date", "")
        if linked_date:
            badge = QLabel(linked_date)
            badge.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            badge.setStyleSheet(
                "color: #dcdcdc; background-color: #2a2a2a; "
                "border: 1px solid #3a3a3a; border-radius: 6px; padding: 1px 6px;"
            )
            right_layout.addWidget(badge, 0, Qt.AlignRight)

        updated = note.get("updated_at", "")
        right = QLabel(updated)
        right.setStyleSheet("color: #999; font-size: 10px;")
        right.setAlignment(Qt.AlignRight | Qt.AlignTop)
        right_layout.addWidget(right, 0, Qt.AlignRight)

        layout.addWidget(left, 1)
        layout.addWidget(right_container, 0)
        return widget
