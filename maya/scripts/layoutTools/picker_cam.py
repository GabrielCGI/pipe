import qtpy.QtWidgets as qt
import qtpy.QtGui as qtg
import qtpy.QtCore as qtc
import maya.cmds as cmds
import os



BG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "background.png")



class PickerCam(qt.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Picker Cam")

        self._canvas = qt.QWidget()
        self.setCentralWidget(self._canvas)

        self.layout_main = qt.QVBoxLayout(self._canvas)
        self.layout_main.setContentsMargins(2 ,0 ,2 ,0)
        self.layout_main.setSpacing(4)


        namespace_lay = qt.QHBoxLayout()
        namespace_lay.setContentsMargins(0 ,0 ,0 ,0)
        self.layout_main.addLayout(namespace_lay)

        self.combo = qt.QComboBox()
        self.combo.addItems(self._findAllReference())
        self.combo.setCurrentText(self._setDefaultNameSpace())
        namespace_lay.addWidget(self.combo)

        refresh = qt.QPushButton("refresh")
        refresh.setMaximumWidth(60)
        refresh.clicked.connect(self._refresh)
        namespace_lay.addWidget(refresh)


        self.layout_main.addStretch()
        titre("main Ctrls", self.layout_main)
        separator(self.layout_main)
        

        self._add_button("World",    [149, 26 , 48 ], True, lambda n: self._selectCTRL(["World_Ctr"]))
        self._add_button("Main",     [0  , 122, 0  ], True, lambda n: self._selectCTRL(["MAIN_Ctr"]))
        self._add_button("trans",    [255, 255, 0  ], False, lambda n: self._selectCTRL(["TRANS_Ctr"]))
        self._add_button("Pan Tilt", [0  , 255, 0  ], False, lambda n: self._selectCTRL(["PAN_TILT_Ctr"]))
        self._add_button("Roll",     [26 , 26 , 128], True, lambda n: self._selectCTRL(["ROLL_Ctr"]))
        
        
        self.layout_main.addStretch()
        titre("Offset Ctrls", self.layout_main)
        separator(self.layout_main)
        
        
        self._add_button("Trans Offset",    [128, 204, 255], False, lambda n: self._selectCTRL(["TRANS_OFFSET_Ctr"]))
        self._add_button("Pan Tilt Offset", [247, 0  , 0  ], False, lambda n: self._selectCTRL(["PAN_TILT_OFFSET_Ctr"]))
        self._add_button("Roll Offset",     [26 , 26 , 128], True, lambda n: self._selectCTRL(["ROLL_OFFSET_Ctr"]))


        self.layout_main.addStretch()
        separator(self.layout_main)

        self._add_button("ALL", [40 , 40 , 40 ], True, lambda n: self._selectCTRL(["World_Ctr", "MAIN_Ctr", "TRANS_Ctr", "PAN_TILT_Ctr", "ROLL_Ctr", "TRANS_OFFSET_Ctr", "PAN_TILT_OFFSET_Ctr", "ROLL_OFFSET_Ctr"]))

    def _refresh(self):
        self.combo.clear()
        self.combo.addItems(self._findAllReference())

    def _add_button(self, text, color, fg, callback):
        btn = qt.QPushButton(text)
        btn.setStyleSheet(f"background-color: rgb({color[0]}, {color[1]}, {color[2]}); color: {'white'if fg else 'black'}")
        btn.clicked.connect(callback)
        self.layout_main.addWidget(btn)
        return btn

    # --- Callbacks (à brancher sur tes fonctions de caméra) ---
    def _selectCTRL(self, name_ctrl: list[str]):
        namespace = self.combo.currentText()
        if namespace == "no NameSpace":
            namespace = ""
        
        cmds.select(clear=True)
        for ctrl in name_ctrl:
            cmds.select(f"{namespace}:{ctrl}", add=True)

    def _findAllReference(self) -> str:
        return [n for n in cmds.namespaceInfo(":", listOnlyNamespaces=True, recurse=True)if n not in ["UI", "shared"]] + ["no NameSpace"]
    
    def _setDefaultNameSpace(self) -> str:
        sel = cmds.ls(sl=True)
        if not sel:
            return ""
        
        return sel[0].split("|")[0].split(":")[0]



def separator(layout: qt.QVBoxLayout):
    separator = qt.QFrame()
    separator.setFrameShape(qt.QFrame.HLine)
    separator.setFrameShadow(qt.QFrame.Sunken)
    separator.setStyleSheet("background-color: #555555;")
    separator.setFixedHeight(2)
    layout.addWidget(separator)


def titre(text: str, layout: qt.QVBoxLayout):
    l_offset = qt.QLabel(text)
    l_offset.setAlignment(qtc.Qt.AlignCenter)
    l_offset.setStyleSheet("""
    font-size: 14px;
    padding: 5px 14px;
    """)
    layout.addWidget(l_offset)