"""
Calendar Page
Shows a calendar and entries for the selected date.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QListWidget, QListWidgetItem, QPushButton, QLineEdit,
    QFormLayout, QComboBox, QTextEdit, QMessageBox, QSizePolicy, QCalendarWidget
)
from PySide6.QtCore import Qt, QDate, QTimer, QDateTime, Signal
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QPainter

from controllers.calendar_controller import CalendarController
from services.calendar_service import CalendarService
from services.notes_service import NotesService


class CalendarPage(QWidget):
    """Calendar page UI."""

    entry_selected = Signal(dict)

    def __init__(self):
        super().__init__()
        self.controller = CalendarController()
        self.service = self.controller.service
        self.notes_service = NotesService()
        self._selected_entry_id = None
        self._selected_entry = None
        self._last_entry_snapshot = None
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Left: calendar widget
        left_panel = QVBoxLayout()
        self.calendar = QDate.currentDate()
        self.calendar_widget = self._build_calendar_widget()
        self.calendar_widget.setMinimumWidth(380)
        left_panel.addWidget(self.calendar_widget)

        # Right: entries + detail
        right_panel = QVBoxLayout()

        header = QLabel("Lịch")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        right_panel.addWidget(header)

        date_search_row = QHBoxLayout()
        self.date_search_input = QLineEdit()
        self.date_search_input.setPlaceholderText("Nhập ngày (dd/MM/yyyy)")
        self.date_search_input.returnPressed.connect(self.on_date_search)
        self.date_search_button = QPushButton("Tới ngày")
        self.date_search_button.clicked.connect(self.on_date_search)
        self.today_button = QPushButton("Hôm nay")
        self.today_button.clicked.connect(self.on_today)
        date_search_row.addWidget(self.date_search_input)
        date_search_row.addWidget(self.date_search_button)
        date_search_row.addWidget(self.today_button)
        right_panel.addLayout(date_search_row)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tìm kiếm theo tiêu đề/ghi chú...")
        self.search_input.textChanged.connect(self.on_search)
        search_row.addWidget(self.search_input)
        right_panel.addLayout(search_row)

        entries_group = QGroupBox("Danh sách sự kiện")
        entries_layout = QVBoxLayout(entries_group)
        self.entries_list = QListWidget()
        self.entries_list.itemSelectionChanged.connect(self.on_entry_selected)
        entries_layout.addWidget(self.entries_list)
        entries_group.setMaximumHeight(200)
        right_panel.addWidget(entries_group, 0)

        self.add_button = QPushButton("Thêm sự kiện")
        self.add_button.clicked.connect(self.add_entry)
        right_panel.addWidget(self.add_button)

        detail_group = QGroupBox("Chi tiết")
        detail_layout = QVBoxLayout(detail_group)
        detail_layout.setSpacing(8)
        self.detail_title = QLineEdit()
        self.detail_time = QLineEdit()
        self.detail_type = QComboBox()
        self.detail_type.addItems(["Task", "Reminder", "Alarm", "Note"])
        self.detail_repeat = QComboBox()
        self.detail_repeat.addItems(["Không", "Hàng ngày", "Hàng tuần", "Hàng tháng", "Hàng năm"])
        self.detail_note = QTextEdit()
        self.detail_note.setMinimumHeight(80)
        self.detail_note.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.detail_created = QLabel("--")
        self.detail_modified = QLabel("--")

        detail_layout.addLayout(self._make_row("Tiêu đề", self.detail_title))
        detail_layout.addLayout(self._make_row("Thời gian", self.detail_time))
        detail_layout.addLayout(self._make_row("Loại", self.detail_type))
        detail_layout.addLayout(self._make_row("Lặp lại", self.detail_repeat))
        detail_layout.addLayout(self._make_row("Ngày tạo", self.detail_created))
        detail_layout.addLayout(self._make_row("Chỉnh sửa", self.detail_modified))

        note_row = QVBoxLayout()
        note_label = QLabel("Ghi chú")
        note_row.addWidget(note_label)
        note_row.addWidget(self.detail_note)
        detail_layout.addLayout(note_row)
        self.save_note_button = QPushButton("Lưu ghi chú")
        self.redo_note_button = QPushButton("Hoàn tác")
        self.delete_note_button = QPushButton("Xóa ghi chú")
        self.open_note_button = QPushButton("Mở ghi chú")
        self.open_note_button.setEnabled(False)
        note_button_row = QHBoxLayout()
        note_button_row.addWidget(self.save_note_button)
        note_button_row.addWidget(self.redo_note_button)
        note_button_row.addWidget(self.delete_note_button)
        note_button_row.addWidget(self.open_note_button)
        detail_layout.addLayout(note_button_row)
        self.save_note_button.clicked.connect(self.save_entry)
        self.redo_note_button.clicked.connect(self.redo_entry)
        self.delete_note_button.clicked.connect(self.delete_entry)
        self.open_note_button.clicked.connect(self.open_note)
        right_panel.addWidget(detail_group)

        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 2)

        self._notified_ids = set()
        self._reminder_timer = QTimer(self)
        self._reminder_timer.setInterval(60 * 1000)
        self._reminder_timer.timeout.connect(self.check_reminders)
        self._reminder_timer.start()

        self.refresh_entries()
        self.refresh_date_markers()

    def _build_calendar_widget(self):
        widget = _MarkedCalendarWidget()
        widget.setSelectedDate(QDate.currentDate())
        widget.selectionChanged.connect(self.on_date_changed)
        widget.setStyleSheet("""

            QCalendarWidget QToolButton#qt_calendar_monthbutton {
                border: 1px solid transparent;
                padding: 2px 6px;
            }
            QCalendarWidget QToolButton#qt_calendar_monthbutton:hover {
                border: 1px solid #3a3a3a;
                border-radius: 4px;
            }
            QCalendarWidget QToolButton#qt_calendar_yearbutton {
                border: 1px solid transparent;
                padding: 2px 6px;
            }
            QCalendarWidget QToolButton#qt_calendar_yearbutton:hover {
                border: 1px solid #3a3a3a;
                border-radius: 4px;
            }
            QCalendarWidget QToolButton::menu-indicator {
                image: none;
                width: 0px;
            }
        """)
        weekend_format = QTextCharFormat()
        weekend_format.setForeground(QColor("#e6e6e6"))
        widget.setWeekdayTextFormat(Qt.Saturday, weekend_format)
        widget.setWeekdayTextFormat(Qt.Sunday, weekend_format)

        return widget

    def _current_date_str(self) -> str:
        date = self.calendar_widget.selectedDate()
        return date.toString("dd/MM/yyyy")

    def refresh_entries(self):
        self.entries_list.clear()
        date_str = self._current_date_str()
        entries = self.controller.get_entries_for_date(date_str)
        entries = self._expand_repeats(entries, date_str)
        entries = self._sort_entries(entries)
        for entry in entries:
            list_item = QListWidgetItem()
            list_item.setData(Qt.UserRole, entry)
            widget = self._create_entry_item_widget(entry)
            list_item.setSizeHint(widget.sizeHint())
            self.entries_list.addItem(list_item)
            self.entries_list.setItemWidget(list_item, widget)
        self.refresh_date_markers()
        self.check_reminders()

    def on_date_changed(self):
        self.refresh_entries()
        self.refresh_date_markers()

    def on_search(self, text: str):
        if not text.strip():
            self.refresh_entries()
            return
        self.entries_list.clear()
        entries = self._sort_entries(self.controller.search_entries(text))
        for entry in entries:
            list_item = QListWidgetItem()
            list_item.setData(Qt.UserRole, entry)
            widget = self._create_entry_item_widget(entry)
            list_item.setSizeHint(widget.sizeHint())
            self.entries_list.addItem(list_item)
            self.entries_list.setItemWidget(list_item, widget)

    def on_entry_selected(self):
        items = self.entries_list.selectedItems()
        if not items:
            return
        entry = items[0].data(Qt.UserRole) or {}
        self._selected_entry_id = entry.get("id")
        self._last_entry_snapshot = entry.copy()
        self._selected_entry = entry
        self.detail_title.setText(entry.get("title", ""))
        self.detail_time.setText(entry.get("time", ""))
        self.detail_type.setCurrentText(entry.get("type", "Task"))
        self.detail_repeat.setCurrentText(self._repeat_label(entry.get("repeat", "none")))
        self.detail_note.setPlainText(entry.get("note", ""))
        self.detail_created.setText(entry.get("created_at", "--"))
        self.detail_modified.setText(entry.get("updated_at", "--"))
        self.open_note_button.setEnabled(entry.get("note_id") is not None)

    def add_entry(self):
        now = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss")
        entry = {
            "id": self.service.generate_id("entry"),
            "date": self._current_date_str(),
            "title": "Sự kiện mới",
            "time": "",
            "type": "Task",
            "repeat": "none",
            "note": "",
            "created_at": now,
            "updated_at": now,
        }
        if self.controller.add_entry(entry):
            self.refresh_entries()
            self._select_entry_by_id(entry["id"])

    def save_entry(self):
        now = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss")
        date_str = self._current_date_str()
        entry_type = self.detail_type.currentText()
        repeat_value = self._repeat_value(self.detail_repeat.currentText())
        title = self.detail_title.text().strip() or "Không tiêu đề"
        time_text = self.detail_time.text().strip()
        note_text = self.detail_note.toPlainText().strip()

        existing_id = getattr(self, "_selected_entry_id", None)
        existing_note_id = None
        if getattr(self, "_last_entry_snapshot", None):
            existing_note_id = self._last_entry_snapshot.get("note_id")

        if entry_type == "Note":
            note_id = existing_note_id or self.notes_service.generate_id("note")
            entry_id = f"note_{note_id}"
        else:
            note_id = None
            entry_id = existing_id or self.service.generate_id("entry")

        created_at = self._last_entry_snapshot.get("created_at") if getattr(self, "_last_entry_snapshot", None) else now
        entry = {
            "id": entry_id,
            "date": date_str,
            "title": title,
            "time": time_text,
            "type": entry_type,
            "repeat": repeat_value,
            "note": note_text,
            "created_at": created_at,
            "updated_at": now,
        }
        if note_id:
            entry["note_id"] = note_id

        confirm = QMessageBox.question(
            self,
            "Lưu sự kiện",
            "Bạn có chắc muốn lưu sự kiện này?" if not existing_id else "Bạn có chắc muốn lưu thay đổi?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        if existing_id:
            self.controller.delete_entry(existing_id)

        self.controller.add_entry(entry)

        if entry_type == "Note":
            note_payload = {
                "id": note_id,
                "title": title,
                "linked_date": date_str,
                "content": note_text,
                "created_at": created_at,
                "updated_at": now,
            }
            self.notes_service.update_note(note_payload)

        self.refresh_entries()
        self.refresh_date_markers()
        self._select_entry_by_id(entry_id)

    def redo_entry(self):
        snapshot = getattr(self, "_last_entry_snapshot", None)
        if not snapshot:
            return
        self.detail_title.setText(snapshot.get("title", ""))
        self.detail_time.setText(snapshot.get("time", ""))
        self.detail_type.setCurrentText(snapshot.get("type", "Task"))
        self.detail_repeat.setCurrentText(self._repeat_label(snapshot.get("repeat", "none")))
        self.detail_note.setPlainText(snapshot.get("note", ""))
        self.detail_created.setText(snapshot.get("created_at", "--"))
        self.detail_modified.setText(snapshot.get("updated_at", "--"))

    def delete_entry(self):
        entry_id = getattr(self, "_selected_entry_id", None)
        if not entry_id:
            return
        confirm = QMessageBox.question(
            self,
            "Xóa sự kiện",
            "Bạn có chắc muốn xóa sự kiện này?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        if self.controller.delete_entry(entry_id):
            self.entries_list.clear()
            self.refresh_entries()
            self.refresh_date_markers()
        self.open_note_button.setEnabled(False)

    def _sort_entries(self, entries):
        def key(item):
            updated = item.get("updated_at", "")
            ts = self._parse_datetime(updated)
            if ts is not None:
                return -ts
            return 0
        return sorted(entries, key=key)

    def _parse_datetime(self, text: str):
        if not text:
            return None
        for fmt in ("dd/MM/yyyy HH:mm:ss", "dd/MM/yyyy HH:mm"):
            dt = QDateTime.fromString(text, fmt)
            if dt.isValid():
                return dt.toSecsSinceEpoch()
        return None

    def _make_row(self, label_text: str, widget):
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(90)
        row.addWidget(label)
        row.addWidget(widget, 1)
        return row

    def _create_entry_item_widget(self, entry: dict) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        title = entry.get("title", "Không tiêu đề")
        time = entry.get("time", "")
        entry_type = entry.get("type", "Task")
        left_text = f"{time} [{entry_type}] {title}".strip()
        left = QLabel(left_text)
        left.setWordWrap(True)
        if entry.get("date") == QDate.currentDate().toString("dd/MM/yyyy"):
            left.setStyleSheet("color: #ffd27d;")

        updated = entry.get("updated_at", "")
        right = QLabel(updated)
        right.setStyleSheet("color: #999; font-size: 10px;")
        right.setAlignment(Qt.AlignRight | Qt.AlignTop)

        layout.addWidget(left, 1)
        layout.addWidget(right, 0)
        return widget

    def _parse_time_minutes(self, time_text: str) -> int:
        try:
            parts = time_text.strip().split(":")
            if len(parts) >= 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2]) if len(parts) >= 3 else 0
                return hours * 3600 + minutes * 60 + seconds
        except Exception:
            pass
        return 24 * 60 * 60  # push invalid times to end

    def _repeat_value(self, label: str) -> str:
        mapping = {
            "Không": "none",
            "Hàng ngày": "daily",
            "Hàng tuần": "weekly",
            "Hàng tháng": "monthly",
            "Hàng năm": "yearly",
        }
        return mapping.get(label, "none")

    def _repeat_label(self, value: str) -> str:
        mapping = {
            "none": "Không",
            "daily": "Hàng ngày",
            "weekly": "Hàng tuần",
            "monthly": "Hàng tháng",
            "yearly": "Hàng năm",
        }
        return mapping.get(value, "Không")

    def _expand_repeats(self, entries, date_str: str):
        selected = QDate.fromString(date_str, "dd/MM/yyyy")
        if not selected.isValid():
            return entries
        expanded = list(entries)
        # Include repeated entries that start before selected date.
        all_items = self.controller.service._load_data()
        for entry in all_items:
            repeat = entry.get("repeat", "none")
            if repeat == "none":
                continue
            start = QDate.fromString(entry.get("date", ""), "dd/MM/yyyy")
            if not start.isValid() or start > selected:
                continue
            if entry.get("date") == date_str:
                continue
            if repeat == "daily":
                expanded.append(entry)
            elif repeat == "weekly":
                days = start.daysTo(selected)
                if days % 7 == 0:
                    expanded.append(entry)
            elif repeat == "monthly":
                if start.day() == selected.day():
                    expanded.append(entry)
            elif repeat == "yearly":
                if start.day() == selected.day() and start.month() == selected.month():
                    expanded.append(entry)
        return expanded

    def check_reminders(self):
        now = QDateTime.currentDateTime()
        today_str = now.date().toString("dd/MM/yyyy")
        entries = self.controller.get_entries_for_date(today_str)
        entries = self._expand_repeats(entries, today_str)
        reminders = []
        alarms = []
        for entry in entries:
            if entry.get("type") not in ("Reminder", "Alarm"):
                continue
            time_text = entry.get("time", "")
            if not time_text:
                key = f"{entry.get('id')}_startup"
                if key in self._notified_ids:
                    continue
                self._notified_ids.add(key)
                if entry.get("type") == "Reminder":
                    reminders.append(entry)
                else:
                    alarms.append(entry)
                continue
            due = QDateTime.fromString(f"{today_str} {time_text}", "dd/MM/yyyy HH:mm:ss")
            if not due.isValid():
                due = QDateTime.fromString(f"{today_str} {time_text}", "dd/MM/yyyy HH:mm")
            if not due.isValid():
                continue
            key = f"{entry.get('id')}_{today_str}"
            if due <= now and key not in self._notified_ids:
                self._notified_ids.add(key)
                if entry.get("type") == "Reminder":
                    reminders.append(entry)
                else:
                    alarms.append(entry)

        if reminders:
            lines = "\n".join([f"- {e.get('title', 'Không tiêu đề')}" for e in reminders])
            QMessageBox.information(self, "Nhắc Nhở:", lines)
        if alarms:
            lines = "\n".join([f"- {e.get('title', 'Không tiêu đề')}" for e in alarms])
            QMessageBox.information(self, "Báo Thức:", lines)

    def on_date_search(self):
        text = self.date_search_input.text().strip()
        if not text:
            return
        date = QDate.fromString(text, "dd/MM/yyyy")
        if date.isValid():
            self.calendar_widget.setSelectedDate(date)
            self.calendar_widget.showSelectedDate()
            self.refresh_date_markers()

    def on_today(self):
        today = QDate.currentDate()
        self.calendar_widget.setSelectedDate(today)
        self.calendar_widget.showSelectedDate()
        self.refresh_date_markers()

    def jump_to_date(self, date_str: str):
        date = QDate.fromString(date_str, "dd/MM/yyyy")
        if date.isValid():
            self.calendar_widget.setSelectedDate(date)
            self.calendar_widget.showSelectedDate()
            self.refresh_entries()
            self.refresh_date_markers()

    def refresh_date_markers(self):
        all_items = self.controller.service._load_data()
        marked = {}
        today = QDate.currentDate()
        end = today.addMonths(2)
        for entry in all_items:
            start = QDate.fromString(entry.get("date", ""), "dd/MM/yyyy")
            if not start.isValid():
                continue
            repeat = entry.get("repeat", "none")
            dates = []
            if repeat == "none":
                dates = [start]
            elif repeat == "daily":
                d = start
                while d <= end:
                    dates.append(d)
                    d = d.addDays(1)
            elif repeat == "weekly":
                d = start
                while d <= end:
                    dates.append(d)
                    d = d.addDays(7)
            elif repeat == "monthly":
                d = start
                while d <= end:
                    if d.day() == start.day():
                        dates.append(d)
                    d = d.addMonths(1)
            elif repeat == "yearly":
                d = start
                while d <= end:
                    if d.day() == start.day() and d.month() == start.month():
                        dates.append(d)
                    d = d.addYears(1)
            for d in dates:
                marked.setdefault(d, set()).add(entry.get("type", "Task"))
        if isinstance(self.calendar_widget, _MarkedCalendarWidget):
            self.calendar_widget.set_marked_dates(marked)

    def _select_entry_by_id(self, entry_id: str):
        for i in range(self.entries_list.count()):
            item = self.entries_list.item(i)
            data = item.data(Qt.UserRole) or {}
            if data.get("id") == entry_id:
                self.entries_list.setCurrentItem(item)
                break

    def open_note(self):
        entry = getattr(self, "_selected_entry", None)
        if not entry:
            return
        if entry.get("note_id"):
            self.entry_selected.emit(entry)


class _MarkedCalendarWidget(QCalendarWidget):
    def __init__(self):
        super().__init__()
        self._marked_dates = {}

    def set_marked_dates(self, dates):
        self._marked_dates = dict(dates)
        self.update()

    def paintCell(self, painter: QPainter, rect, date):
        super().paintCell(painter, rect, date)
        types = self._marked_dates.get(date)
        if types:
            color_map = {
                "Task": "#2a5dff",
                "Reminder": "#2ecc71",
                "Alarm": "#e74c3c",
                "Note": "#f1c40f",
            }
            dots = [color_map.get(t, "#2a5dff") for t in sorted(types)]
            radius = 3
            gap = 2
            total = len(dots) * (radius * 2) + (len(dots) - 1) * gap
            x = rect.right() - total - 2
            y = rect.bottom() - radius * 2 - 2
            painter.save()
            painter.setPen(Qt.NoPen)
            for i, color in enumerate(dots[:3]):
                painter.setBrush(QColor(color))
                cx = x + i * (radius * 2 + gap)
                painter.drawEllipse(cx, y, radius * 2, radius * 2)
            painter.restore()
