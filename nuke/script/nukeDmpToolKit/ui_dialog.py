"""
ui_dialog.py
Dialog de selection des nodes d'entree (Source, CG, Camera).

Deux implementations :
  - StyledSelectionDialog : QDialog dark theme avec sections visuelles (defaut)
  - LayersTo3DPanel       : PythonPanel legacy (fallback)

Compatible PySide2 (Nuke <= 15) et PySide6 (Nuke >= 16).
"""

import nuke
import nukescripts

_CG_NONE_LABEL = "\u2014 None \u2014"

_USE_PYSIDE6 = nuke.NUKE_VERSION_MAJOR >= 16

_STYLESHEET = """
QDialog {
    background: #282828;
    color: #cccccc;
    font-size: 12px;
}
QLabel {
    color: #cccccc;
}
QLabel#sectionTitle {
    font-size: 13px;
    font-weight: bold;
    color: #80dddd;
    padding-bottom: 2px;
}
QFrame#sectionFrame {
    background: #323232;
    border: 1px solid #444444;
    border-radius: 6px;
    padding: 10px;
}
QComboBox {
    background: #3a3a3a;
    color: #cccccc;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 22px;
}
QComboBox:hover {
    border: 1px solid #80dddd;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background: #3a3a3a;
    color: #cccccc;
    selection-background-color: #80dddd;
    selection-color: #282828;
}
QCheckBox {
    color: #cccccc;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555555;
    border-radius: 3px;
    background: #3a3a3a;
}
QCheckBox::indicator:checked {
    background: #80dddd;
    border: 1px solid #80dddd;
}
QPushButton {
    background: #80dddd;
    color: #282828;
    border: none;
    border-radius: 4px;
    padding: 6px 20px;
    font-weight: bold;
    min-height: 24px;
}
QPushButton:hover {
    background: #99e5e5;
}
QPushButton:pressed {
    background: #66cccc;
}
QPushButton#cancelBtn {
    background: #444444;
    color: #cccccc;
}
QPushButton#cancelBtn:hover {
    background: #555555;
}
QLabel#infoText {
    color: #888888;
    font-style: italic;
    font-size: 11px;
}
"""


def _import_qt():
    """Importe QtWidgets et QtCore depuis le bon PySide."""
    if _USE_PYSIDE6:
        from PySide6 import QtWidgets, QtCore
    else:
        from PySide2 import QtWidgets, QtCore
    return QtWidgets, QtCore


def show_selection_dialog():
    """
    Ouvre le dialog de selection style.
    Retourne un dict ou None si annule.
    """
    source_names, cg_names = _get_read_nodes_by_type()
    camera_names = _get_camera_nodes()

    if not source_names:
        nuke.message("Aucun Read node PSD ou EXR multi-layer trouve.")
        return None

    if not camera_names:
        nuke.message("Aucun Camera node trouve dans le script.")
        return None

    QtWidgets, QtCore = _import_qt()
    Qt = QtCore.Qt

    parent = QtWidgets.QApplication.activeWindow()

    class StyledSelectionDialog(QtWidgets.QDialog):

        def __init__(self, par=None):
            super().__init__(par)
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.setWindowTitle("Pimp my DMP")
            self.setMinimumWidth(420)
            self.setStyleSheet(_STYLESHEET)

            layout = QtWidgets.QVBoxLayout(self)
            layout.setSpacing(12)
            layout.setContentsMargins(20, 16, 20, 16)

            # -- Title ---------------------------------------------------------
            title_html = (
                '<div style="text-align: center;">'
                '<font color="#80dddd" size="6">P</font>'
                '<font color="#88dede" size="6">i</font>'
                '<font color="#90dede" size="6">m</font>'
                '<font color="#98dfdf" size="6">p</font>'
                '<font color="#a0dfdf" size="6"> </font>'
                '<font color="#a4dfdf" size="6">m</font>'
                '<font color="#a8e0e0" size="6">y</font>'
                '<font color="#ace0e0" size="6"> </font>'
                '<font color="#b0e0e0" size="6">D</font>'
                '<font color="#b8e1e1" size="6">M</font>'
                '<font color="#c0e1e1" size="6">P</font>'
                '</div>'
            )
            title = QtWidgets.QLabel(title_html)
            title.setAlignment(Qt.AlignCenter if not _USE_PYSIDE6
                               else Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)

            # -- Section SOURCE ------------------------------------------------
            src_frame = QtWidgets.QFrame()
            src_frame.setObjectName("sectionFrame")
            src_layout = QtWidgets.QVBoxLayout(src_frame)
            src_layout.setSpacing(6)

            src_title = QtWidgets.QLabel("SOURCE")
            src_title.setObjectName("sectionTitle")
            src_layout.addWidget(src_title)

            self.source_combo = QtWidgets.QComboBox()
            self.source_combo.addItems(source_names)
            src_layout.addWidget(self.source_combo)

            layout.addWidget(src_frame)

            # -- Section CG REFERENCE ------------------------------------------
            cg_frame = QtWidgets.QFrame()
            cg_frame.setObjectName("sectionFrame")
            cg_layout = QtWidgets.QVBoxLayout(cg_frame)
            cg_layout.setSpacing(6)

            cg_title = QtWidgets.QLabel("CG REFERENCE")
            cg_title.setObjectName("sectionTitle")
            cg_layout.addWidget(cg_title)

            self.cg_combo = QtWidgets.QComboBox()
            self.cg_combo.addItems(cg_names)
            cg_layout.addWidget(self.cg_combo)

            cg_info = QtWidgets.QLabel("Optional — provides depth_extra.z for auto depth range")
            cg_info.setObjectName("infoText")
            cg_layout.addWidget(cg_info)

            layout.addWidget(cg_frame)

            # -- Section CAMERA ------------------------------------------------
            cam_frame = QtWidgets.QFrame()
            cam_frame.setObjectName("sectionFrame")
            cam_layout = QtWidgets.QVBoxLayout(cam_frame)
            cam_layout.setSpacing(6)

            cam_title = QtWidgets.QLabel("CAMERA")
            cam_title.setObjectName("sectionTitle")
            cam_layout.addWidget(cam_title)

            self.camera_combo = QtWidgets.QComboBox()
            self.camera_combo.addItems(camera_names)
            cam_layout.addWidget(self.camera_combo)

            layout.addWidget(cam_frame)

            # -- Section OPTIONS -----------------------------------------------
            opt_frame = QtWidgets.QFrame()
            opt_frame.setObjectName("sectionFrame")
            opt_layout = QtWidgets.QVBoxLayout(opt_frame)
            opt_layout.setSpacing(6)

            opt_title = QtWidgets.QLabel("OPTIONS")
            opt_title.setObjectName("sectionTitle")
            opt_layout.addWidget(opt_title)

            self.group_check = QtWidgets.QCheckBox("Enable layer grouping")
            opt_layout.addWidget(self.group_check)

            self.stamps_check = QtWidgets.QCheckBox("Use Stamps")
            opt_layout.addWidget(self.stamps_check)

            self.info_label = QtWidgets.QLabel("One card per layer will be created.")
            self.info_label.setObjectName("infoText")
            opt_layout.addWidget(self.info_label)

            self.group_check.stateChanged.connect(self._on_group_changed)

            layout.addWidget(opt_frame)

            # -- Buttons -------------------------------------------------------
            btn_layout = QtWidgets.QHBoxLayout()
            btn_layout.addStretch()

            cancel_btn = QtWidgets.QPushButton("Cancel")
            cancel_btn.setObjectName("cancelBtn")
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)

            ok_btn = QtWidgets.QPushButton("OK")
            ok_btn.clicked.connect(self.accept)
            btn_layout.addWidget(ok_btn)

            layout.addLayout(btn_layout)

        def _on_group_changed(self, state):
            if self.group_check.isChecked():
                self.info_label.setText(
                    "One card per group will be created.\n"
                    "You will create groups after clicking OK.")
            else:
                self.info_label.setText("One card per layer will be created.")

    dialog = StyledSelectionDialog(parent)

    if _USE_PYSIDE6:
        accepted = dialog.exec()
    else:
        accepted = dialog.exec_()

    if accepted:
        source_node = nuke.toNode(dialog.source_combo.currentText())
        source_type = _detect_source_type(source_node)
        cg_text = dialog.cg_combo.currentText()
        return {
            "source_node":     source_node,
            "source_type":     source_type,
            "cg_node":         None if cg_text == _CG_NONE_LABEL
                               else nuke.toNode(cg_text),
            "camera_node":     nuke.toNode(dialog.camera_combo.currentText()),
            "enable_grouping": dialog.group_check.isChecked(),
            "use_stamps":      dialog.stamps_check.isChecked(),
        }

    return None


# --------------------------------------------------------------------------
#  Legacy PythonPanel (backup)
# --------------------------------------------------------------------------

class _LayersTo3DPanel_Legacy(nukescripts.PythonPanel):

    def __init__(self, source_names, cg_names, camera_names):
        super(_LayersTo3DPanel_Legacy, self).__init__("Layers to 3D Cards")

        self.source_knob = nuke.Enumeration_Knob("source_node", "Source (PSD / EXR)", source_names)
        self.cg_knob     = nuke.Enumeration_Knob("cg_node",     "CG Reference (EXR)", cg_names)
        self.camera_knob = nuke.Enumeration_Knob("camera_node", "Camera (USD)",       camera_names)

        self.group_knob = nuke.Boolean_Knob("enable_grouping", "Enable layer grouping")
        self.group_knob.setFlag(nuke.STARTLINE)
        self.group_knob.setValue(False)

        self.stamps_knob = nuke.Boolean_Knob("use_stamps", "Use Stamps")
        self.stamps_knob.setFlag(nuke.STARTLINE)
        self.stamps_knob.setValue(False)

        self.divider = nuke.Text_Knob("divider", "")
        self.info_knob = nuke.Text_Knob("info", "",
            '<i><font color="#999999">One card per layer will be created.</font></i>')

        for k in [self.source_knob, self.cg_knob, self.camera_knob,
                  self.group_knob, self.stamps_knob,
                  self.divider, self.info_knob]:
            self.addKnob(k)

    def knobChanged(self, knob):
        if knob is self.group_knob:
            if self.group_knob.value():
                self.info_knob.setValue(
                    '<i><font color="#999999">'
                    'One card per group layer will be created,<br>'
                    'you will be able to create your groups after clicking OK.'
                    '</font></i>')
            else:
                self.info_knob.setValue(
                    '<i><font color="#999999">'
                    'One card per layer will be created.'
                    '</font></i>')


def show_selection_dialog_legacy():
    """
    Ouvre le panel legacy de selection.
    Retourne un dict ou None si annule.
    """
    source_names, cg_names = _get_read_nodes_by_type()
    camera_names = _get_camera_nodes()

    if not source_names:
        nuke.message("Aucun Read node PSD ou EXR multi-layer trouve.")
        return None

    if not camera_names:
        nuke.message("Aucun Camera node trouve dans le script.")
        return None

    panel = _LayersTo3DPanel_Legacy(source_names, cg_names, camera_names)
    if panel.showModalDialog():
        source_node = nuke.toNode(panel.source_knob.value())
        source_type = _detect_source_type(source_node)
        return {
            "source_node":      source_node,
            "source_type":      source_type,
            "cg_node":          None if panel.cg_knob.value() == _CG_NONE_LABEL
                                else nuke.toNode(panel.cg_knob.value()),
            "camera_node":      nuke.toNode(panel.camera_knob.value()),
            "enable_grouping":  panel.group_knob.value(),
            "use_stamps":       panel.stamps_knob.value(),
        }

    return None


# --------------------------------------------------------------------------
#  Validation & helpers
# --------------------------------------------------------------------------

def validate_inputs(source_node, source_type, cg_node, camera_node):
    """
    Valide les nodes selectionnes.
    Retourne (True, "", depth_channel) si OK, ou (False, message_erreur, None).
    """
    if source_node is None or camera_node is None:
        return False, "Un ou plusieurs nodes selectionnes sont invalides.", None

    if source_type not in ("psd", "exr"):
        return False, "Le node '{}' n'est ni un PSD ni un EXR multi-layer.".format(
            source_node.name()), None

    # Depth channel : detecte automatiquement si CG present
    depth_channel = None
    if cg_node is not None:
        depth_channels = [ch for ch in cg_node.channels()
                          if ch.startswith("depth_extra.")]
        if depth_channels:
            depth_channel = depth_channels[0]

    focal = camera_node["focal"].getValue() if camera_node.knob("focal") else 0
    haperture = camera_node["haperture"].getValue() if camera_node.knob("haperture") else 0
    if focal <= 0 or haperture <= 0:
        return False, (
            "Le Camera node '{}' a des valeurs focal/haperture invalides.".format(
                camera_node.name())
        ), None

    return True, "", depth_channel


def _detect_source_type(node):
    """Detecte si un Read node est un PSD ou un EXR."""
    ft_knob = node.knob("file_type")
    if ft_knob and ft_knob.value() == "psd":
        return "psd"
    return "exr"


def _get_read_nodes_by_type():
    """
    Separe les Read nodes en sources (PSD + EXR multi-layer) et CG (EXR).
    Les EXR apparaissent dans les deux listes (peuvent servir de source ou de CG).
    Retourne (source_names, cg_names).
    """
    source_names = []
    cg_names = [_CG_NONE_LABEL]

    for node in nuke.allNodes("Read"):
        ft_knob = node.knob("file_type")
        if ft_knob and ft_knob.value() == "psd":
            source_names.append(node.name())
        else:
            source_names.append(node.name())
            cg_names.append(node.name())

    return source_names, cg_names


def _get_camera_nodes():
    """
    Retourne les noms de tous les Camera2, Camera3 et Camera4 dans le script.
    """
    cameras = []
    for cls in ("Camera2", "Camera3", "Camera4"):
        cameras.extend(n.name() for n in nuke.allNodes(cls))
    return cameras


def show_depth_range_dialog(default_min=100.0, default_max=1000.0):
    """
    PythonPanel pour saisir manuellement les valeurs min/max de profondeur.
    Affiche quand il n'y a pas de passe Z disponible.
    Retourne (min_depth, max_depth) ou None si annule.
    """
    panel = nukescripts.PythonPanel("Depth Range (no Z pass)")

    info = nuke.Text_Knob("info", "",
        '<i><font color="#999999">'
        'No depth_extra pass found.<br>'
        'Cards will be distributed linearly between min and max depth.'
        '</font></i>')

    min_knob = nuke.Double_Knob("min_depth", "Min Depth")
    min_knob.setRange(0.1, 10000.0)
    min_knob.setValue(default_min)

    max_knob = nuke.Double_Knob("max_depth", "Max Depth")
    max_knob.setRange(0.1, 10000.0)
    max_knob.setValue(default_max)

    for k in [info, min_knob, max_knob]:
        panel.addKnob(k)

    if panel.showModalDialog():
        min_d = min_knob.value()
        max_d = max_knob.value()
        if min_d >= max_d:
            nuke.message("Min depth doit etre inferieur a max depth.")
            return None
        return min_d, max_d

    return None
