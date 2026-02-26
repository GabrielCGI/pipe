from hutil.PySide import QtWidgets, QtGui, QtCore
import hou
import webbrowser


class LPEDesigner(QtWidgets.QWidget):

    def __init__(self):
        super(LPEDesigner, self).__init__()

        main_layout = QtWidgets.QVBoxLayout()

        # ---------------- Presets ----------------
        preset_layout = QtWidgets.QHBoxLayout()

        self.btn_reflect = QtWidgets.QPushButton("Reflections")
        self.btn_refract = QtWidgets.QPushButton("Refractions")
        self.btn_transmission = QtWidgets.QPushButton("Transmission")
        self.btn_indirect = QtWidgets.QPushButton("Indirect Only")

        preset_layout.addWidget(self.btn_reflect)
        preset_layout.addWidget(self.btn_refract)
        preset_layout.addWidget(self.btn_transmission)
        preset_layout.addWidget(self.btn_indirect)

        main_layout.addLayout(preset_layout)

        # ---------------- Tag ----------------
        tag_layout = QtWidgets.QHBoxLayout()
        self.tag_input = QtWidgets.QLineEdit()
        tag_layout.addWidget(QtWidgets.QLabel("Tag:"))
        tag_layout.addWidget(self.tag_input)
        main_layout.addLayout(tag_layout)

        # ---------------- Events ----------------
        self.cb_reflect = QtWidgets.QCheckBox("Reflection (R)")
        self.cb_transmit = QtWidgets.QCheckBox("Transmission (T)")
        self.cb_diffuse = QtWidgets.QCheckBox("Diffuse (D)")
        self.cb_glossy = QtWidgets.QCheckBox("Glossy (G)")

        main_layout.addWidget(self.cb_reflect)
        main_layout.addWidget(self.cb_transmit)
        main_layout.addWidget(self.cb_diffuse)
        main_layout.addWidget(self.cb_glossy)

        # ---------------- Repetition ----------------
        self.rep_combo = QtWidgets.QComboBox()
        self.rep_combo.addItems(["Once", "One or More (+)", "Zero or More (*)"])
        main_layout.addWidget(self.rep_combo)

        # ---------------- After Tag (EXCLUSIFS) ----------------
        self.after_combo = QtWidgets.QComboBox()
        self.after_combo.addItems(["None", "Allow after tag (.*)", "Require after tag (.+)"])
        main_layout.addWidget(self.after_combo)
        
        # ---------------- End Condition ----------------
        self.end_light = QtWidgets.QCheckBox("End on Light (L)")
        self.end_light.setChecked(True)
        main_layout.addWidget(self.end_light)

        # ---------------- OUTPUT (affiche la fonction LPE) ----------------
        output_layout = QtWidgets.QVBoxLayout()
        output_layout.addWidget(QtWidgets.QLabel("Generated LPE:"))
        
        self.lpe_output = QtWidgets.QLineEdit()
        self.lpe_output.setReadOnly(True)
        self.lpe_output.setStyleSheet("background-color: #2a2a2a; color: #00ff00; font-family: monospace;")
        output_layout.addWidget(self.lpe_output)
        
        # Bouton Copy
        self.btn_copy = QtWidgets.QPushButton("Copy to Clipboard")
        output_layout.addWidget(self.btn_copy)
        
        main_layout.addLayout(output_layout)

        # ---------------- Node Path Input ----------------
        node_layout = QtWidgets.QVBoxLayout()
        node_layout.addWidget(QtWidgets.QLabel("Target Node Path:"))
        
        node_input_layout = QtWidgets.QHBoxLayout()
        self.node_path_input = QtWidgets.QLineEdit()
        self.node_path_input.setPlaceholderText("/obj/geo1/karmarendersettings1")
        node_input_layout.addWidget(self.node_path_input)
        
        self.btn_use_selected = QtWidgets.QPushButton("Use Selected")
        node_input_layout.addWidget(self.btn_use_selected)
        
        node_layout.addLayout(node_input_layout)
        
        # Checkbox pour activer/désactiver l'auto-apply
        self.cb_auto_apply = QtWidgets.QCheckBox("Auto-apply to node (live update)")
        self.cb_auto_apply.setChecked(True)
        node_layout.addWidget(self.cb_auto_apply)
        
        main_layout.addLayout(node_layout)

        # ---------------- Documentation Link ----------------
        doc_layout = QtWidgets.QHBoxLayout()
        doc_layout.addStretch()
        
        self.btn_doc = QtWidgets.QPushButton("📖 How to add a Render Var (LPE)")
        self.btn_doc.setStyleSheet("color: #4a9eff; text-decoration: underline;")
        self.btn_doc.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))  # CORRECTION ICI
        doc_layout.addWidget(self.btn_doc)
        
        doc_layout.addStretch()
        main_layout.addLayout(doc_layout)

        # Stretch pour pousser tout en haut
        main_layout.addStretch()

        self.setLayout(main_layout)

        # Connect
        self.connect_signals()

        # Initial generation
        self.generate_lpe()

    # =========================
    # SIGNALS
    # =========================

    def connect_signals(self):

        widgets = [
            self.tag_input,
            self.cb_reflect,
            self.cb_transmit,
            self.cb_diffuse,
            self.cb_glossy,
            self.rep_combo,
            self.after_combo,
            self.end_light
        ]

        for w in widgets:
            if isinstance(w, QtWidgets.QLineEdit):
                w.textChanged.connect(self.generate_lpe)
            elif isinstance(w, QtWidgets.QComboBox):
                w.currentIndexChanged.connect(self.generate_lpe)
            else:
                w.stateChanged.connect(self.generate_lpe)

        # Node path input trigger aussi le generate
        self.node_path_input.textChanged.connect(self.generate_lpe)

        # Presets
        self.btn_reflect.clicked.connect(self.preset_reflect)
        self.btn_refract.clicked.connect(self.preset_refract)
        self.btn_transmission.clicked.connect(self.preset_transmission)
        self.btn_indirect.clicked.connect(self.preset_indirect)
        
        # Copy & Use Selected
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.btn_use_selected.clicked.connect(self.use_selected_node)
        
        # Documentation
        self.btn_doc.clicked.connect(self.open_documentation)

    # =========================
    # PRESETS
    # =========================

    def clear_events(self):
        self.cb_reflect.setChecked(False)
        self.cb_transmit.setChecked(False)
        self.cb_diffuse.setChecked(False)
        self.cb_glossy.setChecked(False)

    def preset_reflect(self):
        self.clear_events()
        self.cb_reflect.setChecked(True)
        self.rep_combo.setCurrentIndex(0)
        self.after_combo.setCurrentIndex(0)  # None

    def preset_refract(self):
        self.clear_events()
        self.cb_transmit.setChecked(True)
        self.rep_combo.setCurrentIndex(1)
        self.after_combo.setCurrentIndex(0)  # None

    def preset_transmission(self):
        self.clear_events()
        self.cb_transmit.setChecked(True)
        self.rep_combo.setCurrentIndex(1)  # One or More (+)
        self.after_combo.setCurrentIndex(2)  # Require after tag (.+)
        self.end_light.setChecked(True)

    def preset_indirect(self):
        self.rep_combo.setCurrentIndex(1)
        self.after_combo.setCurrentIndex(2)  # Require after tag (.+)

    # =========================
    # LPE GENERATION
    # =========================

    def build_event_block(self):
        events = []

        if self.cb_reflect.isChecked():
            events.append("R")
        if self.cb_transmit.isChecked():
            events.append("T")
        if self.cb_diffuse.isChecked():
            events.append("D")
        if self.cb_glossy.isChecked():
            events.append("G")

        if not events:
            return ""

        block = "<" + "".join(events) + ">"

        rep_mode = self.rep_combo.currentIndex()
        if rep_mode == 1:
            block += "+"
        elif rep_mode == 2:
            block += "*"

        return block

    def generate_lpe(self):

        lpe = "C"
        lpe += self.build_event_block()

        tag = self.tag_input.text().strip()
        if tag:
            lpe += f"'{tag}'"

            # After tag combo (EXCLUSIF)
            after_mode = self.after_combo.currentIndex()
            if after_mode == 1:  # Allow after tag (.*)
                lpe += ".*"
            elif after_mode == 2:  # Require after tag (.+)
                lpe += ".+"

        # Ajoute le L final si coché
        if self.end_light.isChecked():
            lpe += "L"
    
        # Affiche dans le champ output
        self.lpe_output.setText(lpe)
        
        # Auto-apply si activé
        if self.cb_auto_apply.isChecked():
            self.apply_to_node(lpe)

    # =========================
    # CLIPBOARD & NODE ACTIONS
    # =========================

    def copy_to_clipboard(self):
        """Copie la LPE dans le presse-papier"""
        lpe = self.lpe_output.text()
        QtWidgets.QApplication.clipboard().setText(lpe)
        hou.ui.setStatusMessage(f"Copied: {lpe}", severity=hou.severityType.Message)

    def use_selected_node(self):
        """Remplit le champ avec le node sélectionné"""
        selected = hou.selectedNodes()
        if not selected:
            hou.ui.displayMessage("No node selected", severity=hou.severityType.Warning)
            return
        
        self.node_path_input.setText(selected[0].path())

    def apply_to_node(self, lpe):
        """Applique la LPE au node spécifié (silencieux si auto-apply)"""
        node_path = self.node_path_input.text().strip()
        
        if not node_path:
            return  # Silencieux si pas de node path
        
        try:
            node = hou.node(node_path)
            
            if not node:
                return
            
            if node.type().name() != "karmarendersettings":
                return
            
            parm = node.parm("sourceName1")
            if parm:
                parm.set(lpe)
                
        except Exception:
            pass  # Silencieux pour ne pas spammer les erreurs

    def open_documentation(self):
        """Ouvre la documentation sur comment ajouter une Render Var"""
        # URL vers la doc SideFX officielle
        url = "https://www.notion.so/illogic/Karma-LPE-3069d24ae7e380bb8ae0f502ab1b5a98?source=copy_link"
        webbrowser.open(url)
        hou.ui.setStatusMessage("Opening documentation in browser...", severity=hou.severityType.Message)


def createInterface():
    return LPEDesigner()