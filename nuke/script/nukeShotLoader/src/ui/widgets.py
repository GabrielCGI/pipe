"""Reusable widgets, delegates and small builders shared by the tabs."""

import os
import subprocess

from ..core.config import Config
from .qt import QtCore, QtGui, QtWidgets
from ..scene import utils as scene
from . import icons

# Item data roles used by the Render Manager tables.
NODE_ROLE = QtCore.Qt.UserRole          # node fullName
PREFIX_ROLE = QtCore.Qt.UserRole + 1    # UI-only identifier prefix ("precomp_")
RAW_ROLE = QtCore.Qt.UserRole + 2       # last value known on the node
WARNING_ROLE = QtCore.Qt.UserRole + 3   # duplicate-identifier flag


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def button(text, slot=None, object_name=None, tooltip=None):
    btn = QtWidgets.QPushButton(text)
    btn.setCursor(QtCore.Qt.PointingHandCursor)
    if object_name:
        btn.setObjectName(object_name)
    if tooltip:
        btn.setToolTip(tooltip)
    if slot is not None:
        btn.clicked.connect(slot)
    return btn


def icon_button(object_name, size, slot=None):
    btn = QtWidgets.QPushButton()
    btn.setObjectName(object_name)
    btn.setCursor(QtCore.Qt.PointingHandCursor)
    btn.setFixedSize(*size)
    btn.setIconSize(QtCore.QSize(14, 14))
    if slot is not None:
        btn.clicked.connect(slot)
    return btn


def centered(widget):
    """Wrap a cell widget so the cell's spare space doesn't stretch it."""
    cell = QtWidgets.QWidget()
    layout = QtWidgets.QHBoxLayout(cell)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(QtCore.Qt.AlignCenter)
    layout.addWidget(widget)
    return cell


def read_only_item(text, bold=False):
    item = QtWidgets.QTableWidgetItem(text)
    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
    if bold:
        font = item.font()
        font.setBold(True)
        item.setFont(font)
    return item


def set_background(item, color):
    """Solid background, or the alternating row color when `color` is None."""
    item.setBackground(QtGui.QColor(color) if color else QtGui.QBrush())


def select_rows(table, rows, clear=True):
    """Select whole rows in one selection-model update."""
    model = table.model()
    last_col = table.columnCount() - 1
    selection = QtCore.QItemSelection()
    for row in rows:
        selection.select(model.index(row, 0), model.index(row, last_col))
    flags = QtCore.QItemSelectionModel.Rows | (
        QtCore.QItemSelectionModel.ClearAndSelect if clear else QtCore.QItemSelectionModel.Select)
    table.selectionModel().select(selection, flags)


def ensure_row_selected(table, row):
    """Right-click on an unselected row selects just that row, so context
    actions never ignore the row under the cursor."""
    if not any(idx.row() == row for idx in table.selectionModel().selectedRows()):
        select_rows(table, [row])


def open_in_explorer(parent, entries):
    """Open one Explorer window per distinct folder of (label, folder)
    entries; unresolved ones are reported in a single dialog."""
    seen, opened, missing = set(), 0, []
    for label, folder in entries:
        if not folder:
            missing.append(label)
            continue
        folder = os.path.normpath(folder)
        if folder in seen:
            continue
        seen.add(folder)
        if not os.path.exists(folder):
            missing.append(f"{label} ({folder})")
            continue
        try:
            subprocess.Popen(['explorer', folder])
            print(f"[ShotAssetLoader] Opened folder in Explorer: {folder}")
            opened += 1
        except Exception as e:
            missing.append(f"{label}: {e}")
    if missing:
        more = f"\n... and {len(missing) - 10} more" if len(missing) > 10 else ""
        QtWidgets.QMessageBox.warning(
            parent, "Some Folders Missing",
            f"Opened {opened} folder(s); could not resolve:\n" + "\n".join(missing[:10]) + more)


def fit_height_delta(table, rows):
    """Extra dialog height needed so `rows` rows fit without scrolling."""
    row_h = table.verticalHeader().defaultSectionSize()
    header_h = table.horizontalHeader().height() or 30
    desired = header_h + rows * row_h + table.frameWidth() * 2 + 6
    return desired - table.height()


# ---------------------------------------------------------------------------
# Header widgets
# ---------------------------------------------------------------------------

def project_header(session):
    """Framed strip: project thumbnail, project name, studio logo."""
    frame = QtWidgets.QFrame()
    frame.setObjectName("projectTitle")
    layout = QtWidgets.QHBoxLayout(frame)
    layout.setContentsMargins(18, 12, 18, 12)
    layout.setSpacing(12)

    if session.project_detected:
        thumbnail = icons.rounded_pixmap(
            os.path.join(session.project_root, *Config.PROJECT_THUMBNAIL.split("/")), height=56)
        if thumbnail is not None:
            layout.addWidget(_pixmap_label(thumbnail), alignment=QtCore.Qt.AlignVCenter)

    title = QtWidgets.QLabel()
    title.setTextFormat(QtCore.Qt.RichText)
    title.setText(
        '<span style="font-size:10px; color:#8a8a8a; letter-spacing:2.5px; font-weight:600;">'
        'PROJECT</span><br>'
        f'<span style="font-size:20px; color:#f0f0f0; font-weight:700; letter-spacing:0.5px;">'
        f'{session.project_name}</span>'
    )
    layout.addWidget(title)
    layout.addStretch()

    logo = icons.faded_pixmap(Config.LOGO_PATH, height=56, opacity=Config.LOGO_OPACITY)
    if logo is not None:
        layout.addWidget(_pixmap_label(logo), alignment=QtCore.Qt.AlignVCenter)
    return frame


def _pixmap_label(pixmap):
    label = QtWidgets.QLabel()
    label.setPixmap(pixmap)
    label.setFixedSize(pixmap.size())
    return label


class ContextBanner(QtWidgets.QFrame):
    """SHOT / FRAMES / FPS / FORMAT / <count> chip strip. Extra widgets
    (e.g. the package picker) can be appended on the right."""

    _CHIP = ("<span style='color:#9a9a9a; font-size:10px; letter-spacing:1.2px;'>{}</span>"
             " &nbsp;<span style='color:#ffffff;'>{}</span>")
    _SEPARATOR = " &nbsp;&nbsp;&nbsp;&nbsp; "

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("headerBanner")
        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setContentsMargins(14, 10, 14, 10)
        self._layout.setSpacing(12)
        self._label = QtWidgets.QLabel("Detecting shot context from script path…")
        self._label.setObjectName("bannerText")
        self._label.setTextFormat(QtCore.Qt.RichText)
        self._layout.addWidget(self._label)
        self._layout.addStretch()

    def add_widget(self, widget):
        self._layout.addWidget(widget)

    def set_message(self, text):
        self._label.setText(text)

    def show_shot(self, session, count_label, count):
        """Chips read from the current scene (what the artist works in)."""
        if not session.has_shot:
            return
        frame_range = scene.scene_frame_range()
        fps = scene.scene_fps()
        fmt = scene.scene_format()
        chips = [
            ("SHOT", f"<b>{session.sequence}</b> / <b>{session.shot}</b>"),
            ("FRAMES", f"{frame_range[0]}-{frame_range[1]}" if frame_range else "Unknown"),
            ("FPS", "Unknown" if fps is None else (f"{int(fps)}" if fps.is_integer() else f"{fps:g}")),
            ("FORMAT", f"{fmt[0]}x{fmt[1]}" if fmt else "Unknown"),
            (count_label, str(count)),
        ]
        self._label.setText(self._SEPARATOR.join(self._CHIP.format(*chip) for chip in chips))


# ---------------------------------------------------------------------------
# Delegates / widgets
# ---------------------------------------------------------------------------

class StatusColorDelegate(QtWidgets.QStyledItemDelegate):
    """Keeps a cell's status color visible when its row is selected."""

    def paint(self, painter, option, index):
        bg = index.data(QtCore.Qt.BackgroundRole)
        if isinstance(bg, QtGui.QBrush) and bg.color().alpha() > 0:
            opt = QtWidgets.QStyleOptionViewItem(option)
            self.initStyleOption(opt, index)
            opt.state &= ~QtWidgets.QStyle.State_Selected
            opt.backgroundBrush = bg
            super().paint(painter, opt, index)
            return
        super().paint(painter, option, index)


class TallEditorDelegate(QtWidgets.QStyledItemDelegate):
    """Inline editor taller than the 28px row (width unchanged, so the
    neighbouring columns stay visible while editing)."""

    def __init__(self, min_editor_height=32, parent=None):
        super().__init__(parent)
        self._min_height = min_editor_height

    def updateEditorGeometry(self, editor, option, index):
        rect = QtCore.QRect(option.rect)
        if rect.height() < self._min_height:
            rect.setTop(rect.top() - (self._min_height - rect.height()) // 2)
            rect.setHeight(self._min_height)
        editor.setGeometry(rect)


class IdentifierDelegate(TallEditorDelegate):
    """Precomp Identifier column: warning icon on the RIGHT of duplicated
    rows (WARNING_ROLE), and an editor that only exposes the raw suffix so
    the 'precomp_' prefix can't be altered."""

    def __init__(self, icon_size=14, parent=None):
        super().__init__(parent=parent)
        self._icon_size = icon_size

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if not index.data(WARNING_ROLE):
            return
        rect = option.rect
        icon_rect = QtCore.QRect(rect.right() - self._icon_size - 4,
                                 rect.top() + (rect.height() - self._icon_size) // 2,
                                 self._icon_size, self._icon_size)
        icons.warning_icon().paint(painter, icon_rect)

    def setEditorData(self, editor, index):
        if isinstance(editor, QtWidgets.QLineEdit):
            prefix = index.data(PREFIX_ROLE) or ""
            text = index.data(QtCore.Qt.DisplayRole) or ""
            if prefix and text.startswith(prefix):
                text = text[len(prefix):]
            editor.setText(text)
            editor.selectAll()
            return
        super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QtWidgets.QLineEdit):
            prefix = index.data(PREFIX_ROLE) or ""
            raw = (editor.text() or "").strip()
            model.setData(index, f"{prefix}{raw}" if raw else "", QtCore.Qt.DisplayRole)
            return
        super().setModelData(editor, model, index)


class PackageComboBox(QtWidgets.QComboBox):
    """Shows only the bare package name (UserRole) when collapsed; the
    popup keeps the full 'PKG_v001    (v053 / 09/07/26)' text."""

    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        painter.setPen(self.palette().color(QtGui.QPalette.Text))
        opt = QtWidgets.QStyleOptionComboBox()
        self.initStyleOption(opt)
        short = self.itemData(self.currentIndex(), QtCore.Qt.UserRole) if self.currentIndex() >= 0 else None
        if short:
            opt.currentText = short
        painter.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, opt)
        painter.drawControl(QtWidgets.QStyle.CE_ComboBoxLabel, opt)
