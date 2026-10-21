"""
Location Selection Page
Allows users to select their province and region in Vietnam
"""

from pathlib import Path
import sys

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox,
    QGridLayout, QMessageBox, QCompleter, QSizePolicy,
    QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsItem, QToolTip
)
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QFont, QPainter, QPainterPath, QColor, QPen, QBrush, QTransform

try:
    from controllers.location_controller import LocationController
except ModuleNotFoundError:
    try:
        from ...controllers.location_controller import LocationController
    except Exception:
        import sys
        from pathlib import Path

        project_root = Path(__file__).resolve().parents[2]
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from controllers.location_controller import LocationController


def _parse_float(value: str) -> float:
    try:
        cleaned = "".join(ch for ch in value if (ch.isdigit() or ch in ".-"))
        return float(cleaned) if cleaned else 0.0
    except Exception:
        return 0.0


def _parse_color(value: str):
    if not value:
        return None
    value = value.strip()
    if value.lower() == "none":
        return None
    if value.startswith("#"):
        hex_value = value[1:]
        if len(hex_value) == 3:
            hex_value = "".join(ch * 2 for ch in hex_value)
        if len(hex_value) == 6:
            try:
                return QColor(
                    int(hex_value[0:2], 16),
                    int(hex_value[2:4], 16),
                    int(hex_value[4:6], 16),
                )
            except Exception:
                return None
    if value.startswith("rgb"):
        try:
            numbers = value[value.find("(") + 1:value.find(")")].split(",")
            r, g, b = [int(float(n.strip())) for n in numbers[:3]]
            return QColor(r, g, b)
        except Exception:
            return None
    return None


def _parse_style_attr(style: str):
    style_map = {}
    if not style:
        return style_map
    for part in style.split(";"):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        style_map[key.strip()] = value.strip()
    return style_map


def _parse_view_box(root) -> QRectF:
    vb = root.attrib.get("viewBox") or root.attrib.get("viewbox")
    if vb:
        parts = [p for p in vb.replace(",", " ").split() if p]
        if len(parts) == 4:
            return QRectF(
                float(parts[0]),
                float(parts[1]),
                float(parts[2]),
                float(parts[3]),
            )
    width = _parse_float(root.attrib.get("width", "0"))
    height = _parse_float(root.attrib.get("height", "0"))
    return QRectF(0, 0, width, height)


def _normalize_name(name: str) -> str:
    if not name:
        return ""
    try:
        import unicodedata
    except Exception:
        return name.strip().lower()
    normalized = unicodedata.normalize("NFKD", name)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return stripped.strip().lower()


def _svg_path_to_qpath(svg_path):
    try:
        from svg.path import parse_path, Move, Line, CubicBezier, QuadraticBezier, Arc
    except Exception:
        return QPainterPath()

    parsed = parse_path(svg_path)
    qpath = QPainterPath()
    started = False
    current = None

    for segment in parsed:
        if isinstance(segment, Move):
            qpath.moveTo(segment.end.real, segment.end.imag)
            started = True
            current = segment.end
            continue

        if not started:
            qpath.moveTo(segment.start.real, segment.start.imag)
            started = True

        if isinstance(segment, Line):
            qpath.lineTo(segment.end.real, segment.end.imag)
        elif isinstance(segment, CubicBezier):
            qpath.cubicTo(
                segment.control1.real, segment.control1.imag,
                segment.control2.real, segment.control2.imag,
                segment.end.real, segment.end.imag,
            )
        elif isinstance(segment, QuadraticBezier):
            qpath.quadTo(
                segment.control.real, segment.control.imag,
                segment.end.real, segment.end.imag,
            )
        elif isinstance(segment, Arc):
            steps = 20
            for i in range(1, steps + 1):
                pt = segment.point(i / steps)
                qpath.lineTo(pt.real, pt.imag)
        else:
            steps = 12
            for i in range(1, steps + 1):
                pt = segment.point(i / steps)
                qpath.lineTo(pt.real, pt.imag)
        current = segment.end

    return qpath


class ProvincePathItem(QGraphicsPathItem):
    def __init__(
        self,
        path: QPainterPath,
        fill: QColor,
        stroke: QColor,
        stroke_width: float,
        element_id: str,
        display_name: str,
    ):
        super().__init__(path)
        self.element_id = element_id
        self.display_name = display_name
        self._base_brush = QBrush(fill) if fill else QBrush(Qt.transparent)
        self._hover_brush = QBrush(QColor(120, 190, 255, 140))
        self._selected_brush = QBrush(QColor(30, 90, 170, 210))
        self._selected = False
        self.setBrush(self._base_brush)
        if stroke:
            pen = QPen(stroke, stroke_width if stroke_width > 0 else 0.5)
        else:
            pen = QPen(Qt.NoPen)
        self.setPen(pen)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemIsFocusable, False)
        if self.display_name:
            self.setToolTip(self.display_name)

    def set_selected(self, selected: bool):
        self._selected = selected
        if self._selected:
            self.setBrush(self._selected_brush)
        else:
            self.setBrush(self._base_brush)

    def hoverEnterEvent(self, event):
        if not self._selected:
            self.setBrush(self._hover_brush)
        self.setCursor(Qt.PointingHandCursor)
        if self.display_name:
            QToolTip.showText(event.screenPos(), self.display_name)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if self._selected:
            self.setBrush(self._selected_brush)
        else:
            self.setBrush(self._base_brush)
        self.setCursor(Qt.ArrowCursor)
        QToolTip.hideText()
        super().hoverLeaveEvent(event)


class SvgMapView(QGraphicsView):
    """QGraphicsView that renders SVG paths as individual items."""

    province_clicked = Signal(str)
    zoom_changed = Signal(int)

    def __init__(self, svg_path: Path, parent=None):
        super().__init__(parent)
        self.setRenderHints(self.renderHints() | QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setMouseTracking(True)
        self.setMinimumHeight(240)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._view_box = QRectF()
        self._base_transform = None
        self._current_scale = 1.0
        self._min_zoom = 0.5
        self._max_zoom = 6.0
        self._user_zoomed = False
        self._selected_item = None
        self._focused_on_selection = False
        self._full_map_transform = None
        self._items_by_name = {}
        self._items_by_id = {}

        self._load_svg(svg_path)

    def _load_svg(self, svg_path: Path):
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(str(svg_path))
            root = tree.getroot()
        except Exception:
            return

        self._view_box = _parse_view_box(root)
        if self._view_box.isNull():
            return
        self._scene.setSceneRect(self._view_box)

        root_style = _parse_style_attr(root.attrib.get("style", ""))
        default_fill = _parse_color(root.attrib.get("fill")) or _parse_color(root_style.get("fill", ""))
        default_stroke = _parse_color(root.attrib.get("stroke")) or _parse_color(root_style.get("stroke", ""))
        default_stroke_width = _parse_float(
            root.attrib.get("stroke-width", root_style.get("stroke-width", "0"))
        )

        for elem in root.iter():
            if not elem.tag.endswith("path"):
                continue
            d = elem.attrib.get("d")
            if not d:
                continue

            style_map = _parse_style_attr(elem.attrib.get("style", ""))
            fill = _parse_color(elem.attrib.get("fill")) or _parse_color(style_map.get("fill", "")) or default_fill
            stroke = _parse_color(elem.attrib.get("stroke")) or _parse_color(style_map.get("stroke", "")) or default_stroke
            stroke_width = _parse_float(elem.attrib.get("stroke-width", style_map.get("stroke-width", "0")))
            if stroke_width == 0:
                stroke_width = default_stroke_width

            qpath = _svg_path_to_qpath(d)
            if qpath.isEmpty():
                continue

            element_id = elem.attrib.get("id", "")
            display_name = elem.attrib.get("name", "") or element_id
            item = ProvincePathItem(qpath, fill, stroke, stroke_width, element_id, display_name)
            self._scene.addItem(item)
            if display_name:
                self._items_by_name[_normalize_name(display_name)] = item
            if element_id:
                self._items_by_id[element_id] = item

        self._apply_fit()

    def _apply_fit(self):
        if self._view_box.isNull():
            return
        self.resetTransform()
        self.fitInView(self._view_box, Qt.KeepAspectRatio)
        self._full_map_transform = self.transform()
        self._base_transform = self._full_map_transform
        self._current_scale = 1.0
        self._emit_zoom()

    def wheelEvent(self, event):
        if self._view_box.isNull():
            return
        delta = event.angleDelta().y()
        if delta == 0:
            delta = event.pixelDelta().y()
        if delta == 0:
            return
        factor = 1.15 if delta > 0 else 1 / 1.15
        self._apply_zoom_step(factor)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, ProvincePathItem):
            if self._selected_item and self._selected_item is not item:
                self._selected_item.set_selected(False)
            self._selected_item = item
            self._selected_item.set_selected(True)
            if item.display_name:
                self.province_clicked.emit(item.display_name)
        super().mousePressEvent(event)

    def zoom_in(self):
        self._apply_zoom_step(1.15)

    def zoom_out(self):
        self._apply_zoom_step(1 / 1.15)

    def focus_selected(self):
        if not self._selected_item:
            return
        self._focused_on_selection = True
        self._user_zoomed = True
        if self._full_map_transform is None:
            self._apply_fit()
        # Compute a zoom level that fits the selected province, but keep base on full-map transform.
        self.fitInView(self._selected_item.boundingRect(), Qt.KeepAspectRatio)
        selection_transform = self.transform()
        base = QTransform(self._full_map_transform) if self._full_map_transform is not None else QTransform()
        base_scale = base.m11() if base.m11() != 0 else 1.0
        sel_scale = selection_transform.m11() if selection_transform.m11() != 0 else 1.0
        ratio = sel_scale / base_scale
        ratio = max(self._min_zoom, min(self._max_zoom, ratio))
        self._base_transform = base
        self._current_scale = ratio
        base = QTransform(self._base_transform)
        base.scale(self._current_scale, self._current_scale)
        self.setTransform(base)
        self._emit_zoom()

    def focus_full_map(self):
        self._focused_on_selection = False
        self._user_zoomed = False
        self._apply_fit()

    def _apply_zoom_step(self, factor: float):
        if self._view_box.isNull():
            return
        new_scale = self._current_scale * factor
        new_scale = max(self._min_zoom, min(self._max_zoom, new_scale))
        if new_scale == self._current_scale:
            return
        self._current_scale = new_scale
        self._user_zoomed = True
        if self._base_transform is None:
            self._apply_fit()
        base = QTransform(self._base_transform)
        base.scale(self._current_scale, self._current_scale)
        self.setTransform(base)
        self._emit_zoom()

    def _emit_zoom(self):
        percent = int(round(self._current_scale * 100))
        self.zoom_changed.emit(percent)

    def select_province(self, province_name: str):
        """Select a province by name (normalized)."""
        key = _normalize_name(province_name)
        item = self._items_by_name.get(key)
        if item is None and province_name:
            item = self._items_by_id.get(province_name)
        if item is None:
            if self._selected_item:
                self._selected_item.set_selected(False)
                self._selected_item = None
            return
        if self._selected_item and self._selected_item is not item:
            self._selected_item.set_selected(False)
        self._selected_item = item
        self._selected_item.set_selected(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._user_zoomed:
            self._apply_fit()


class LocationPage(QWidget):
    """Location selection page with province dropdown and map"""

    location_changed = Signal(str, str)  # province, region

    def __init__(self):
        super().__init__()
        self.controller = LocationController()
        self.init_ui()
        self.setup_connections()
        self.load_current_location()

    def init_ui(self):
        """Initialize the location selection UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Chọn Vị Trí")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        content_layout = QHBoxLayout()

        # Map display (left)
        map_group = QGroupBox("Bản đồ Việt Nam")
        map_layout = QVBoxLayout(map_group)
        map_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        map_container = QWidget()
        map_container_layout = QHBoxLayout(map_container)
        map_container_layout.setContentsMargins(0, 0, 0, 0)
        map_container_layout.setSpacing(8)

        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(6)

        self.zoom_in_button = QPushButton("+")
        self.zoom_out_button = QPushButton("−")
        self.focus_selected_button = QPushButton("Đã\nchọn")
        self.focus_map_button = QPushButton("Bản\nđồ")
        self.zoom_label = QLabel("100%")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setStyleSheet("color: #d0d0d0; font-size: 11px;")

        for button in (self.zoom_in_button, self.zoom_out_button):
            button.setFixedWidth(40)
            button.setStyleSheet(
                "QPushButton { background: #ffffff; color: #111111; border: 1px solid #cfcfcf; "
                "border-radius: 6px; padding: 6px; }"
                "QPushButton:hover { background: #f0f0f0; }"
            )
        for button in (self.focus_selected_button, self.focus_map_button):
            button.setFixedWidth(40)
            button.setFixedHeight(52)
            button.setStyleSheet(
                "QPushButton { background: #ffffff; color: #111111; border: 1px solid #cfcfcf; "
                "border-radius: 6px; padding: 4px; }"
                "QPushButton:hover { background: #f0f0f0; }"
            )

        self.focus_map_button.setStyleSheet(
            "QPushButton { background: #ffffff; color: #111111; border: 1px solid #cfcfcf; "
            "border-radius: 6px; padding: 4px; }"
            "QPushButton:hover { background: #f0f0f0; }"
        )

        control_layout.addWidget(self.zoom_in_button)
        control_layout.addWidget(self.zoom_out_button)
        control_layout.addWidget(self.focus_selected_button)
        control_layout.addWidget(self.focus_map_button)
        control_layout.addWidget(self.zoom_label)
        control_layout.addStretch()

        self.map_widget = self.build_map_widget()
        map_container_layout.addWidget(control_panel)
        map_container_layout.addWidget(self.map_widget, 1)

        map_layout.addWidget(map_container)

        # Right column (controls + info)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Province selection section
        province_group = QGroupBox("Chọn Tỉnh/Thành Phố")
        province_layout = QVBoxLayout(province_group)

        # Province dropdown
        self.province_combo = QComboBox()
        self.province_combo.setEditable(True)
        self.province_combo.setInsertPolicy(QComboBox.NoInsert)
        self.province_combo.setPlaceholderText("Tìm kiếm hoặc chọn tỉnh...")
        self.populate_provinces()
        province_layout.addWidget(self.province_combo)

        # Region display
        self.region_label = QLabel("Vùng: Chưa chọn")
        self.region_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        province_layout.addWidget(self.region_label)

        # Selected location info
        info_group = QGroupBox("Thông Tin Vị Trí")
        info_layout = QGridLayout(info_group)

        self.province_info = QLabel("Tỉnh: Chưa chọn")
        self.region_info = QLabel("Vùng: Chưa chọn")
        self.coordinates_info = QLabel("Tọa độ: Chưa có")

        info_layout.addWidget(QLabel("Tỉnh đã chọn:"), 0, 0)
        info_layout.addWidget(self.province_info, 0, 1)
        info_layout.addWidget(QLabel("Vùng:"), 1, 0)
        info_layout.addWidget(self.region_info, 1, 1)
        info_layout.addWidget(QLabel("Tọa độ:"), 2, 0)
        info_layout.addWidget(self.coordinates_info, 2, 1)

        # Action buttons
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Lưu Vị Trí")
        self.save_button.clicked.connect(self.save_location)
        self.save_button.setEnabled(False)

        self.clear_button = QPushButton("Xóa")
        self.clear_button.clicked.connect(self.clear_location)

        self.restore_button = QPushButton("Trở về vị trí đã lưu")
        self.restore_button.clicked.connect(self.restore_saved_location)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.restore_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()

        right_layout.addWidget(province_group)
        right_layout.addWidget(info_group)
        right_layout.addLayout(button_layout)
        right_layout.addStretch()

        content_layout.addWidget(map_group, 4)
        content_layout.addWidget(right_panel, 1)
        layout.addLayout(content_layout)

    def populate_provinces(self):
        """Populate the province dropdown using controller"""
        provinces = self.controller.get_all_provinces()
        self.province_combo.addItems(provinces)
        completer = QCompleter(provinces, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.province_combo.setCompleter(completer)

    def setup_connections(self):
        """Setup signal connections"""
        # Controller signals
        self.controller.location_changed.connect(self.on_location_updated)
        self.controller.location_error.connect(self.on_location_error)
        self.controller.location_saved.connect(self.on_location_saved)

        # UI signals
        self.province_combo.currentTextChanged.connect(self.on_province_changed)
        if isinstance(self.map_widget, SvgMapView):
            self.map_widget.province_clicked.connect(self.on_province_clicked)
            self.zoom_in_button.clicked.connect(self.map_widget.zoom_in)
            self.zoom_out_button.clicked.connect(self.map_widget.zoom_out)
            self.focus_selected_button.clicked.connect(self.map_widget.focus_selected)
            self.focus_map_button.clicked.connect(self.map_widget.focus_full_map)
            self.map_widget.zoom_changed.connect(self.on_zoom_changed)

    def on_zoom_changed(self, percent: int):
        self.zoom_label.setText(f"{percent}%")

    def on_province_changed(self, province):
        """Handle province selection change using controller"""
        province = (province or "").strip()
        if not province:
            self.region_label.setText("Vùng: Chưa chọn")
            self.province_info.setText("Tỉnh: Chưa chọn")
            self.region_info.setText("Vùng: Chưa chọn")
            self.coordinates_info.setText("Tọa độ: Chưa có")
            self.save_button.setEnabled(False)
            if isinstance(self.map_widget, SvgMapView):
                self.map_widget.select_province("")
            return

        if not self.controller.validate_province(province):
            self.region_label.setText("Vùng: Không xác định")
            self.province_info.setText(f"Tỉnh: {province}")
            self.region_info.setText("Vùng: Không xác định")
            self.coordinates_info.setText("Tọa độ: Không có")
            self.save_button.setEnabled(False)
            if isinstance(self.map_widget, SvgMapView):
                self.map_widget.select_province(province)
            return

        region = self.controller.get_region_from_province(province)
        coordinates = self.controller.get_coordinates(province)

        self.region_label.setText(f"Vùng: {region or 'Không xác định'}")
        self.province_info.setText(f"Tỉnh: {province}")
        self.region_info.setText(f"Vùng: {region or 'Không xác định'}")

        if coordinates:
            self.coordinates_info.setText(
                f"Tọa độ: {coordinates[0]:.2f}, {coordinates[1]:.2f}"
            )
        else:
            self.coordinates_info.setText("Tọa độ: Không có")

        self.save_button.setEnabled(True)
        if isinstance(self.map_widget, SvgMapView):
            self.map_widget.select_province(province)

    def on_province_clicked(self, province_name: str):
        """Handle map click selection."""
        if not province_name:
            return
        all_provinces = self.controller.get_all_provinces()
        target_key = _normalize_name(province_name)
        matched = None
        for name in all_provinces:
            if _normalize_name(name) == target_key:
                matched = name
                break
        self.province_combo.setCurrentText(matched or province_name)

    def save_location(self):
        """Save the selected location using controller"""
        province = self.province_combo.currentText()
        if province:
            success = self.controller.save_location(province)
            if not success:
                QMessageBox.warning(self, "Lỗi", "Không thể lưu vị trí")

    def clear_location(self):
        """Clear the selected location using controller"""
        success = self.controller.clear_location()
        if success:
            self.province_combo.setCurrentText("")

    def load_current_location(self):
        """Load and display current saved location using controller"""
        if self.controller.load_saved_location():
            current_location = self.controller.get_current_location()
            self._apply_saved_location(current_location)

    def restore_saved_location(self):
        """Restore saved location and update map + UI."""
        if not self.controller.load_saved_location():
            QMessageBox.information(self, "Thông báo", "Chưa có vị trí đã lưu.")
            return
        current_location = self.controller.get_current_location()
        self._apply_saved_location(current_location)

    def _apply_saved_location(self, current_location):
        province = current_location.get("province")
        region = current_location.get("region")
        coordinates = current_location.get("coordinates")

        if province:
            self.province_combo.setCurrentText(province)
            self.province_info.setText(f"Tỉnh: {province}")
            self.region_info.setText(f"Vùng: {region}")

            if coordinates:
                self.coordinates_info.setText(
                    f"Tọa độ: {coordinates[0]:.2f}, {coordinates[1]:.2f}"
                )
            else:
                self.coordinates_info.setText("Tọa độ: Đã lưu")

            self.save_button.setEnabled(True)

    def on_location_updated(self, province, region):
        """Handle location update from controller"""
        self.location_changed.emit(province, region)

    def on_location_error(self, error_message):
        """Handle location error from controller"""
        QMessageBox.critical(self, "Lỗi Vị Trí", error_message)

    def on_location_saved(self):
        """Handle successful location save from controller"""
        QMessageBox.information(
            self,
            "Thành Công",
            "Vị trí đã được lưu thành công",
        )

    def build_map_widget(self) -> QWidget:
        """Build the SVG map widget or a fallback label"""
        if getattr(sys, "frozen", False):
            base_path = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
            app_root = base_path / "farmer_app"
        else:
            app_root = Path(__file__).resolve().parents[2]
        svg_candidates = [
            app_root / "assets" / "vn.svg",
            app_root / "ui" / "assets" / "vn.svg",
        ]

        for svg_path in svg_candidates:
            if svg_path.exists():
                return SvgMapView(svg_path)

        fallback = QLabel(
            "Chưa tìm thấy file `vn.svg`.\n"
            "Hãy đặt file vào `farmer_app/assets/` hoặc `farmer_app/ui/assets/`."
        )
        fallback.setAlignment(Qt.AlignCenter)
        fallback.setStyleSheet("color: #666; padding: 12px;")
        return fallback
