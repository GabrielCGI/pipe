# -*- coding: utf-8 -*-
"""
cfx_recache_ui.py - Standalone picker for the cfx re-cache tool.

Everything is configured in the app (no config.json): the artist picks the .hip,
the Prism project is derived automatically, the tracked layer is chosen from a
dropdown filled from the project's pipeline.json, and other settings are
persisted via QSettings. This UI does NOT load Houdini itself: it runs
recache_cfx.py through hython as a subprocess (QProcess) to read shot state
(--status) and re-cache the selection (--apply).
"""

import os
import re
import sys
import glob
import json
import time
import tempfile

try:
    from PySide6 import QtWidgets, QtGui
    from PySide6.QtCore import (
        Qt,
        QProcess,
        QProcessEnvironment,
        QSettings,
        QThread,
        QTimer,
        Signal,
    )
except ImportError:
    from PySide2 import QtWidgets, QtGui
    from PySide2.QtCore import Qt, QProcess, QProcessEnvironment, QSettings
    from PySide2.QtCore import QThread, QTimer, Signal

from lop_update_cache import preview

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "recache_cfx.py")


def _read_version():
    """Version = celle du package installe (importlib.metadata), sinon lue dans le
    pyproject.toml a la racine du repo. La version est GEREE PAR LA CI du studio
    (auto-bump de `version = "x.y.z"` dans pyproject.toml) -> on la lit, on ne la
    fixe pas ici. Robuste que l'UI tourne installee ou depuis une copie brute."""
    try:
        from importlib.metadata import version

        return version("lop_update_cache")
    except Exception:
        pass
    try:
        # module = <repo>/src/lop_update_cache/x.py -> pyproject a 3 niveaux au-dessus
        root = os.path.dirname(os.path.dirname(HERE))
        with open(os.path.join(root, "pyproject.toml"), encoding="utf-8") as f:
            m = re.search(r'^\s*version\s*=\s*"([^"]+)"', f.read(), re.M)
            return m.group(1) if m else "dev"
    except Exception:
        return "dev"


APP_VERSION = _read_version()

# Produit CONTAINER du shot (.../Export/USD/vNNN/...) : path_layers l'expose comme un
# "layer" a part entiere -> le suivre = suivre le STACK du shot (n'importe quel
# departement qui bouge fait bouger le container).
STACK_LAYER = "USD"
STACK_LABEL = "STACK"  # libelle affiche (dropdown + entete de colonne)

STATUS_START = ">>>STATUS_JSON>>>"
STATUS_END = "<<<STATUS_JSON<<<"
# releves de cache emis par le moteur apres un apply (cf preview.record_state) : c'est
# l'UI qui les ecrit dans le sidecar -> un seul ecrivain de ce fichier.
RECORDS_START = ">>>CACHE_RECORDS>>>"
RECORDS_END = "<<<CACHE_RECORDS<<<"

DEFAULT_SETTINGS = {
    "hython": r"C:\Program Files\Side Effects Software\Houdini 21.0.596\bin\hython.exe",
    "stage_root": "/stage",
    "import_pattern": "{shot}",
    "cache_pattern": "cache_{shot}",
    "import_node_type": "prism::LOP_Import",
    "import_path_parm": "filepath",
    "tracked_layer": "_layer_anm_master",
    "projects_root": "I:/",  # ou scanner les projets Prism (dossiers avec 00_Pipeline)
}

# env vars posees par le shelf tool Houdini pour auto-detecter le contexte courant
ENV_PROJECT = "LOP_UPDATE_CACHE_PROJECT"  # chemin du pipeline.json du projet courant
ENV_HIP = "LOP_UPDATE_CACHE_HIP"  # scene .hip courante (pre-remplissage)

# setting key -> engine flag
SETTING_TO_FLAG = {
    "stage_root": "--stage-root",
    "import_pattern": "--import-pattern",
    "cache_pattern": "--cache-pattern",
    "import_node_type": "--import-node-type",
    "import_path_parm": "--import-path-parm",
    "tracked_layer": "--tracked-layer",
}

SETTING_HELP = {
    "hython": "Path to hython.exe used to run the engine.\n"
    "Auto-detected from your Houdini installs if left at a missing path.",
    "project_override": "Prism project.\n"
    "'(auto-detect)' = the project passed by Houdini when launched from the shelf, "
    "or derived by walking up from the .hip to a 00_Pipeline/pipeline.json.\n"
    "Otherwise pick a project from the list (folders with 00_Pipeline under I:/).",
    "stage_root": "LOP network root scanned for cache nodes (default /stage).",
    "import_pattern": "Legacy naming hint only. Pairing is done by shot: each "
    "cache is matched to the import that imports the same shot (node names ignored).",
    "cache_pattern": "Legacy naming hint only. Pairing is done by shot content.",
    "import_node_type": "Node type considered an import (default prism::LOP_Import). "
    "All imports of this type are indexed by the shot they import.",
    "import_path_parm": "Parameter on the import node holding the USD path "
    "(default filepath).",
}

STATE_TEXT = {
    "outdated": "OUTDATED",
    "uptodate": "up to date",
    "no_layer": "n/a (not consumed)",
    "no_import": "n/a (no import)",
    # jamais caché par l'outil -> aucun relevé, donc rien à affirmer (cf preview.record_state)
    "no_record": "? (never cached here)",
    "error": "ERROR",
}

# Le bouton d'action ne fait plus que "recacher" : cfx/fx = re-cache, lighting = re-cache
# + re-render sur la ferme. D'ou un libelle neutre.
APPLY_LABEL = "Update selected shots"

# Animation "ca calcule" : sablier braille (police mono, largeur constante).
SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

# Bornes du buffer stdout (cf _on_out) : au-dela de _BUF_MAX on ne garde que la queue.
_BUF_MAX = 8 * 1024 * 1024
_BUF_KEEP = 4 * 1024 * 1024

# Ce que raconte le moteur -> phase lisible affichee EN BAS pendant le run.
# (motif dans la ligne de log, libelle) ; 1er match gagne, ordre = du + precis au + large.
PHASES = [
    ("Rafraichissement de l'etat", "Refreshing the state of every shot (long)…"),
    ("Etat rafraichi", "State refreshed — finishing…"),
    ("SUBMIT RENDERS", "Submitting to the farm (Deadline)…"),
    ("Scene sauvee", "Saving the scene (Prism version-up)…"),
    ("execute lop_filecache", "Re-caching: publishing the USD layer…"),
    ("re-cache SOP", "Re-simulating the SOP caches…"),
    ("bump import", "Bumping the import to the latest version…"),
    ("Ouverture scene", "Loading the scene in Houdini…"),
    ("Scene chargee", "Scene loaded — analysing the shots…"),
    ("RESUME", "Wrapping up…"),
]


def _fmt_elapsed(sec):
    """'47s' / '2m 05s' / '1h 39m' -- court, lisible d'un coup d'oeil. Passe en HEURES
    au-dela de 60 min (sinon un batch long affiche '878m 00s', illisible)."""
    sec = int(sec)
    if sec < 60:
        return "%ds" % sec
    if sec < 3600:
        return "%dm %02ds" % (sec // 60, sec % 60)
    return "%dh %02dm" % (sec // 3600, (sec % 3600) // 60)


def detect_hython(configured):
    """Return the configured hython if it exists, else the newest installed one.
    'Newest' = tri NUMERIQUE de la version (pas lexical : 21.0.100 > 21.0.99)."""
    if configured and os.path.exists(configured):
        return configured
    found = glob.glob(
        r"C:\Program Files\Side Effects Software\Houdini *\bin\hython.exe"
    )
    if not found:
        return configured or ""

    def _vkey(p):
        m = re.search(r"Houdini ([\d.]+)", p)
        return tuple(int(x) for x in m.group(1).split(".")) if m else ()

    return max(found, key=_vkey)


def derive_project(hip):
    """Walk up from the .hip until a 00_Pipeline/pipeline.json is found."""
    d = os.path.dirname(os.path.abspath(hip)) if hip else ""
    for _ in range(15):
        cand = os.path.join(d, "00_Pipeline", "pipeline.json")
        if os.path.exists(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return ""


def list_prism_projects(root="I:/"):
    """[(nom, chemin pipeline.json)] des projets Prism sous `root` : dossiers de 1er
    niveau contenant 00_Pipeline/pipeline.json. Un seul niveau -> rapide meme en reseau."""
    out = []
    try:
        for name in sorted(os.listdir(root)):
            cfg = os.path.join(root, name, "00_Pipeline", "pipeline.json")
            if os.path.isfile(cfg):
                out.append((name, cfg))
    except Exception:
        pass
    return out


def project_name_of(pipeline_cfg):
    """Nom de projet depuis un chemin .../<projet>/00_Pipeline/pipeline.json."""
    if not pipeline_cfg:
        return ""
    return os.path.basename(os.path.dirname(os.path.dirname(pipeline_cfg)))


def theme_colors(widget):
    """Palette adaptee au theme clair/sombre (Windows). Sur theme CLAIR, des fonds
    sombres rendent le texte illisible -> on prend des fonds PALES ; et l'inverse.
    bg_* = QColor (fond de ligne) ; le reste = couleurs texte (hex, pour styleSheet)."""
    try:
        dark = widget.palette().color(QtGui.QPalette.Window).lightness() < 128
    except Exception:
        dark = True
    if dark:
        return {
            "bg_outdated": QtGui.QColor(70, 45, 0),
            "bg_error": QtGui.QColor(70, 0, 0),
            "bg_gray": QtGui.QColor(45, 45, 45),
            "sop": "#78aae6",
            "green": "#3fae4f",
            "orange": "#e0a020",
            "red": "#e0603a",
            "gray": "#9a9a9a",
        }
    return {
        "bg_outdated": QtGui.QColor(255, 224, 178),
        "bg_error": QtGui.QColor(255, 205, 210),
        "bg_gray": QtGui.QColor(232, 232, 232),
        "sop": "#0d5bbf",
        "green": "#1e7d32",
        "orange": "#a85e00",
        "red": "#c62828",
        "gray": "#5f6b7a",
    }


def _shot_sort_key(d):
    """Tri des shots SQ>SH (SQ0010/SH0010 < SQ0010/SH0020 < SQ0020/SH0090). Les shots
    non resolus ('?') vont en fin."""
    shot = (d.get("shot") or "").strip()
    if not shot or shot == "?":
        return (9, 9999, 9999, "")
    nums = re.findall(r"\d+", shot)
    seq = int(nums[0]) if len(nums) >= 1 else 9999
    sh = int(nums[1]) if len(nums) >= 2 else 9999
    return (0, seq, sh, shot)


def read_departments(project_cfg):
    """Read pipeline.json -> usd.departmentOrder -> [(name, layer_product)].
    Layers follow the _layer_<abbr>_master convention."""
    if not project_cfg or not os.path.exists(project_cfg):
        return []
    try:
        with open(project_cfg, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return []
    order = (data.get("usd") or {}).get("departmentOrder", [])
    out = []
    for d in order:
        abbr = d.get("abbreviation")
        if abbr:
            out.append((d.get("name") or abbr, "_layer_%s_master" % abbr))
    return out


class SettingsDialog(QtWidgets.QDialog):
    """Persisted settings: hython + node convention + reset. (Le PROJET se choisit
    dans le dropdown de la fenetre principale, pas ici.)"""

    def __init__(self, parent, values):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(600)
        form = QtWidgets.QFormLayout(self)

        self.ed_hython = QtWidgets.QLineEdit(values.get("hython", ""))
        b_hy = QtWidgets.QPushButton("...")
        b_hy.clicked.connect(self._pick_hython)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.ed_hython)
        row.addWidget(b_hy)
        self._add_row(form, "hython:", row, SETTING_HELP["hython"])

        form.addRow(QtWidgets.QLabel("<b>Advanced</b> (node convention)"))
        self.ed_stage = QtWidgets.QLineEdit(values.get("stage_root", ""))
        self.ed_imp_pat = QtWidgets.QLineEdit(values.get("import_pattern", ""))
        self.ed_cache_pat = QtWidgets.QLineEdit(values.get("cache_pattern", ""))
        self.ed_imp_type = QtWidgets.QLineEdit(values.get("import_node_type", ""))
        self.ed_path_parm = QtWidgets.QLineEdit(values.get("import_path_parm", ""))
        self._add_row(form, "Stage root:", self.ed_stage, SETTING_HELP["stage_root"])
        self._add_row(
            form, "Import pattern:", self.ed_imp_pat, SETTING_HELP["import_pattern"]
        )
        self._add_row(
            form, "Cache pattern:", self.ed_cache_pat, SETTING_HELP["cache_pattern"]
        )
        self._add_row(
            form,
            "Import node type:",
            self.ed_imp_type,
            SETTING_HELP["import_node_type"],
        )
        self._add_row(
            form,
            "Import path parm:",
            self.ed_path_parm,
            SETTING_HELP["import_path_parm"],
        )

        self.reset_requested = False
        bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        b_reset = QtWidgets.QPushButton("Reset local settings")
        b_reset.setToolTip(
            "Clear ALL saved preferences on this machine: chosen scenes, project, "
            "tracked layer, per-shot SOP cache selections, hython path, window state.\n"
            "Cannot be undone."
        )
        b_reset.clicked.connect(self._reset)
        bb.addButton(b_reset, QtWidgets.QDialogButtonBox.ResetRole)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        form.addRow(bb)

    def _reset(self):
        yes = QtWidgets.QMessageBox.StandardButton.Yes
        if (
            QtWidgets.QMessageBox.question(
                self,
                "Reset local settings",
                "Clear ALL saved preferences (scenes, project, per-shot SOP selections, "
                "hython path)?\nThis cannot be undone.",
            )
            == yes
        ):
            self.reset_requested = True
            self.accept()

    def _add_row(self, form, label_text, field, tip):
        label = QtWidgets.QLabel(label_text)
        label.setToolTip(tip)
        if hasattr(field, "setToolTip"):
            field.setToolTip(tip)
        form.addRow(label, field)

    def _pick_hython(self):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "hython.exe", "", "hython (hython.exe)"
        )
        if p:
            self.ed_hython.setText(p)

    def values(self):
        return {
            "hython": self.ed_hython.text().strip(),
            "stage_root": self.ed_stage.text().strip() or "/stage",
            "import_pattern": self.ed_imp_pat.text().strip() or "{shot}",
            "cache_pattern": self.ed_cache_pat.text().strip() or "cache_{shot}",
            "import_node_type": self.ed_imp_type.text().strip() or "prism::LOP_Import",
            "import_path_parm": self.ed_path_parm.text().strip() or "filepath",
        }


class ProjectPicker(QtWidgets.QDialog):
    """Light project scene picker: cascading Sequence -> Shot -> Department -> Task
    -> Scenefile, built by listing the Prism project folders (no Prism dependency).
    Returns the picked .hip path."""

    LEVELS = ["Sequence", "Shot", "Department", "Task", "Scenefile"]

    # Colonnes a largeur PROPORTIONNELLE au contenu, pas 5 colonnes egales : les noms
    # de scene sont 3x plus longs que les autres niveaux et se faisaient tronquer.
    # Mesure sur yuka_2604 (1249 scenes, police du dialogue), largeur mini utile :
    #   Sequence 96 px | Shot 171 | Department 95 | Task 112 | Scenefile 329
    # Elargir la fenetre ne suffit PAS : a colonnes egales il faudrait 1645 px de large
    # pour que Scenefile tienne, alors que le total reellement necessaire est ~830 px.
    STRETCH = {"Sequence": 2, "Shot": 3, "Department": 2, "Task": 2, "Scenefile": 6}

    def __init__(self, parent, shots_root, current=""):
        super().__init__(parent)
        self.setWindowTitle("Open scene from project")
        self.resize(1034, 550)
        self.shots_root = shots_root
        self._path = ""
        v = QtWidgets.QVBoxLayout(self)
        self.lbl_root = QtWidgets.QLabel(shots_root)
        v.addWidget(self.lbl_root)
        cols = QtWidgets.QHBoxLayout()
        self.lists = []
        for name in self.LEVELS:
            box = QtWidgets.QVBoxLayout()
            box.addWidget(QtWidgets.QLabel(name))
            lw = QtWidgets.QListWidget()
            lw.currentItemChanged.connect(self._on_select)
            box.addWidget(lw)
            cols.addLayout(box, self.STRETCH.get(name, 2))
            self.lists.append(lw)
        self.lists[-1].itemDoubleClicked.connect(lambda *_: self.accept())
        v.addLayout(cols)
        self.bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Open | QtWidgets.QDialogButtonBox.Cancel
        )
        self.bb.button(QtWidgets.QDialogButtonBox.Open).setEnabled(False)
        self.bb.accepted.connect(self.accept)
        self.bb.rejected.connect(self.reject)
        v.addWidget(self.bb)
        self._fill(0, shots_root)
        self._preselect(current)
        if self.lists[0].count() == 0:
            self.lbl_root.setText(
                "%s\n⚠ No sequences here - is this really the project's Shots "
                "folder? (Cancel and pick the folder that contains 03_Production)"
                % shots_root
            )
            self.lbl_root.setStyleSheet("color: %s;" % theme_colors(self)["orange"])

    def selected_path(self):
        return self._path

    @staticmethod
    def _vkey(name):
        m = re.search(r"v(\d+)", name)
        return int(m.group(1)) if m else -1

    def _entries(self, base, files):
        if not base or not os.path.isdir(base):
            return []
        try:
            names = os.listdir(base)
        except Exception:
            return []
        if files:
            hips = [
                n for n in names if n.lower().endswith((".hip", ".hipnc", ".hiplc"))
            ]
            hips.sort(key=self._vkey, reverse=True)
            return [(n, os.path.join(base, n)) for n in hips]
        out = []
        for n in sorted(names):
            # Prism range les scenes de SEQUENCE sous un "shot" special nomme _sequence
            # (ex SQ0010/_sequence/Scenefiles/Lighting/...) -> il faut le MONTRER, sinon
            # les scenes lighting de sequence sont inatteignables. On continue de cacher
            # les autres _*/.* (thumbnails, archives, dossiers techniques).
            if n.startswith(".") or (n.startswith("_") and n != "_sequence"):
                continue
            full = os.path.join(base, n)
            if os.path.isdir(full):
                out.append((n, full))
        return out

    def _fill(self, level, base):
        is_files = level == len(self.LEVELS) - 1
        lw = self.lists[level]
        lw.blockSignals(True)
        lw.clear()
        for down in self.lists[level + 1 :]:
            down.clear()
        for name, full in self._entries(base, is_files):
            it = QtWidgets.QListWidgetItem(name)
            it.setData(Qt.UserRole, full)
            it.setToolTip(name)  # filet de securite si un nom deborde quand meme
            lw.addItem(it)
        lw.blockSignals(False)
        self._path = ""
        self.bb.button(QtWidgets.QDialogButtonBox.Open).setEnabled(False)

    def _on_select(self, cur, _prev=None):
        if cur is None:
            return
        lw = self.sender()
        level = self.lists.index(lw)
        full = cur.data(Qt.UserRole)
        if level == len(self.LEVELS) - 1:
            self._path = full
            self.bb.button(QtWidgets.QDialogButtonBox.Open).setEnabled(True)
            return
        nxt = level + 1
        base = full
        if self.LEVELS[nxt] == "Department":
            base = os.path.join(full, "Scenefiles")
        self._fill(nxt, base)

    def _preselect(self, current):
        if not current:
            return
        p = current.replace("\\", "/")
        m = re.search(r"/Shots/([^/]+)/([^/]+)/Scenefiles/([^/]+)/([^/]+)/", p + "/")
        if not m:
            return
        for level, name in enumerate(list(m.groups()) + [os.path.basename(current)]):
            lw = self.lists[level]
            for i in range(lw.count()):
                if lw.item(i).text() == name:
                    lw.setCurrentRow(i)
                    break


class FxChainDialog(QtWidgets.QDialog):
    """Editeur de la chaine de caches SOP a re-simuler pour un shot FX. Liste cochable
    (defaut = tout coche) ordonnee par topologie ; l'artiste decoche ceux qui n'ont pas
    besoin d'etre re-simules. 'Apply to all shots' propage la selection par POSITION
    (necessite des setups identiques). Retourne la liste ordonnee des 'rel' coches."""

    def __init__(self, parent, shot, chain, checked_rels):
        super().__init__(parent)
        self.setWindowTitle("SOP caches to re-sim - %s" % shot)
        self.resize(560, 420)
        self._apply_all = False
        v = QtWidgets.QVBoxLayout(self)
        v.addWidget(
            QtWidgets.QLabel(
                "Tick the SOP caches to re-simulate (in order). Untick the ones that "
                "don't depend on the anim (rest / collision / source caches)."
            )
        )
        self.listw = QtWidgets.QListWidget()
        for c in chain:
            label = "%s   [%s]" % (c.get("rel") or c.get("name"), c.get("type"))
            it = QtWidgets.QListWidgetItem(label)
            it.setData(Qt.UserRole, c)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            checked = (
                (c.get("rel") in checked_rels) if checked_rels is not None else True
            )
            it.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            self.listw.addItem(it)
        v.addWidget(self.listw, 1)

        row = QtWidgets.QHBoxLayout()
        b_all = QtWidgets.QPushButton("Check all")
        b_all.clicked.connect(lambda: self._set_all(True))
        b_none = QtWidgets.QPushButton("Uncheck all")
        b_none.clicked.connect(lambda: self._set_all(False))
        row.addWidget(b_all)
        row.addWidget(b_none)
        row.addStretch(1)
        self.cb_apply_all = QtWidgets.QCheckBox("Apply this selection to all shots")
        self.cb_apply_all.setToolTip(
            "On OK, copy this tick pattern (by cache position) to every other shot.\n"
            "Assumes the shots share the same cache order."
        )
        row.addWidget(self.cb_apply_all)
        v.addLayout(row)

        bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def _set_all(self, on):
        for i in range(self.listw.count()):
            self.listw.item(i).setCheckState(Qt.Checked if on else Qt.Unchecked)

    def checked_rels(self):
        """Rel-paths coches, dans l'ordre de la liste (= ordre topologique)."""
        out = []
        for i in range(self.listw.count()):
            it = self.listw.item(i)
            if it.checkState() == Qt.Checked:
                out.append((it.data(Qt.UserRole) or {}).get("rel"))
        return [r for r in out if r]

    def checked_mask(self):
        """Masque booleen par POSITION (pour propager aux autres shots)."""
        return [
            self.listw.item(i).checkState() == Qt.Checked
            for i in range(self.listw.count())
        ]

    def apply_to_all(self):
        return self.cb_apply_all.isChecked()


class RenderPickerDialog(QtWidgets.QDialog):
    """Choix des LAYERS (executions) a rendre pour un shot lighting. Une scene lighting a
    UN prism::LOP_Render par shot, dont le multiparm 'executions' liste des layers
    (CHARS/BG/FG/MG/VOLUME...). On coche ceux a rendre ; defaut = ceux actuellement
    Enabled dans le node (behavior 1). Cocher/decocher ecrit le Enabled a l'apply
    (behavior 2). 'Apply to all shots' propage PAR NOM de layer (les layers sont les memes
    d'un shot a l'autre, contrairement aux noms de nodes). Retourne les layers coches."""

    def __init__(self, parent, shot, layers, checked_layers):
        super().__init__(parent)
        self.setWindowTitle("Layers to render - %s" % shot)
        self.resize(560, 400)
        self._apply_all = False
        v = QtWidgets.QVBoxLayout(self)
        v.addWidget(
            QtWidgets.QLabel(
                "Tick the layers (render executions) to render on the farm for this shot.\n"
                "Default = the layers currently enabled on the node. Unticking all = "
                "re-cache only, no render."
            )
        )
        self.listw = QtWidgets.QListWidget()
        for lyr in layers:  # [{layer, enabled}]
            name = lyr.get("layer")
            tag = "" if lyr.get("enabled") else "   (disabled on node)"
            it = QtWidgets.QListWidgetItem("%s%s" % (name, tag))
            it.setData(Qt.UserRole, name)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(
                Qt.Checked if name in (checked_layers or set()) else Qt.Unchecked
            )
            self.listw.addItem(it)
        v.addWidget(self.listw, 1)

        row = QtWidgets.QHBoxLayout()
        b_all = QtWidgets.QPushButton("Check all")
        b_all.clicked.connect(lambda: self._set_all(True))
        b_none = QtWidgets.QPushButton("Uncheck all")
        b_none.clicked.connect(lambda: self._set_all(False))
        row.addWidget(b_all)
        row.addWidget(b_none)
        row.addStretch(1)
        self.cb_apply_all = QtWidgets.QCheckBox("Apply this selection to all shots")
        self.cb_apply_all.setToolTip(
            "On OK, copy this layer selection (by layer name) to every other shot."
        )
        row.addWidget(self.cb_apply_all)
        v.addLayout(row)

        bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def _set_all(self, on):
        for i in range(self.listw.count()):
            self.listw.item(i).setCheckState(Qt.Checked if on else Qt.Unchecked)

    def checked_layers(self):
        out = []
        for i in range(self.listw.count()):
            it = self.listw.item(i)
            if it.checkState() == Qt.Checked:
                out.append(it.data(Qt.UserRole))
        return [n for n in out if n]

    def apply_to_all(self):
        return self.cb_apply_all.isChecked()


class CheckDragTableWidget(QtWidgets.QTableWidget):
    """Table ou un clic-glisse sur la colonne des cases (col 0) 'peint' les cases : la
    1ere case cliquee bascule, et toutes les cases survolees pendant le drag prennent LE
    MEME etat -> cocher/decocher plusieurs shots d'un seul geste."""

    CHECK_COL = 0

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._paint_state = None  # Qt.Checked / Qt.Unchecked pendant un drag

    def _set_row(self, row, state):
        it = self.item(row, self.CHECK_COL)
        if (
            it is not None
            and (it.flags() & Qt.ItemIsUserCheckable)
            and it.checkState() != state
        ):
            it.setCheckState(state)

    def mousePressEvent(self, e):
        idx = self.indexAt(e.pos())
        if (
            e.button() == Qt.LeftButton
            and idx.isValid()
            and idx.column() == self.CHECK_COL
        ):
            it = self.item(idx.row(), self.CHECK_COL)
            if it is not None and (it.flags() & Qt.ItemIsUserCheckable):
                self._paint_state = (
                    Qt.Unchecked if it.checkState() == Qt.Checked else Qt.Checked
                )
                self._set_row(idx.row(), self._paint_state)
                return  # on gere le toggle nous-memes (pas de toggle natif en plus)
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._paint_state is not None:
            idx = self.indexAt(e.pos())
            if idx.isValid() and idx.column() == self.CHECK_COL:
                self._set_row(idx.row(), self._paint_state)
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._paint_state = None
        super().mouseReleaseEvent(e)


class _ScanWorker(QThread):
    """Scan disque (glob des vNNN + parse des containers .usda) HORS du thread UI ->
    ne gele pas sur le reseau. Emet le status rafraichi (gaps de version a jour)."""

    done = Signal(list)

    def __init__(self, status, records=None):
        super().__init__()
        self._status = status
        self._records = records or {}

    def run(self):
        try:
            preview.refresh_status(self._status, self._records)
        except Exception:
            pass
        self.done.emit(self._status)


class Main(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LOP Cache Updater  —  v%s" % APP_VERSION)
        icon = os.path.join(HERE, "cache_updater.png")
        if not os.path.exists(icon):
            icon = r"R:\devToto\shelf\icons\cache_updater.png"
        if os.path.exists(icon):
            self.setWindowIcon(QtGui.QIcon(icon))
        self.resize(1240, 900)
        self.proc = None
        self._buf = ""  # canal COMPLET (parsing STATUS_JSON / SAVED_SCENE)
        self._linebuf = ""  # lignes partielles pour le filtre du log humain
        self._in_status = False  # dans un bloc STATUS_JSON -> masque du log humain
        self._mode = None  # "status" | "apply"
        self._departments = []
        self._data = []  # last status payload; lets us re-render without reloading
        self._populating = False
        self._fx_selection = {}  # shot -> [checked SOP cache rels] (cache in-memory)
        self._render_selection = {}  # shot -> [checked render paths] (cache in-memory)
        self._fx_store = (
            None  # json partage a cote du hip (lazy) : snapshot + selections
        )
        self._scan = None  # _ScanWorker en cours (preview disque en tache de fond)
        self._previewed = None  # hip deja preview (evite les re-preview au keystroke)
        # feedback "ca tourne" : phase courante + chrono + spinner (tick toutes les 200ms)
        self._phase = ""
        self._t0 = None
        self._spin = 0
        self._ticker = QTimer(self)
        self._ticker.setInterval(200)
        self._ticker.timeout.connect(self._tick)
        self.settings = QSettings("Illogic", "lop_update_cache")
        self._load_settings()
        self._build()
        self._on_hip_changed()

    # ---------------------------------------------------------- settings
    def _load_settings(self):
        self.cfg = {}
        for k, dv in DEFAULT_SETTINGS.items():
            self.cfg[k] = self.settings.value(k, dv)
        self.cfg["hython"] = detect_hython(self.cfg.get("hython"))
        self.cfg["project_override"] = self.settings.value("project_override", "")
        self.last_hip = self.settings.value("last_hip", "")
        # lance depuis Houdini : pre-remplir la scene courante si rien de memorise
        if not self.last_hip:
            envhip = os.environ.get(ENV_HIP, "")
            if envhip and os.path.isfile(envhip):
                self.last_hip = envhip

    def _save_settings(self):
        for k in list(DEFAULT_SETTINGS.keys()) + ["project_override"]:
            self.settings.setValue(k, self.cfg.get(k, ""))
        self.settings.setValue("last_hip", self.ed_hip.text().strip())

    # ------------------------------------------------------------------ UI
    def _build(self):
        cw = QtWidgets.QWidget()
        self.setCentralWidget(cw)
        lay = QtWidgets.QVBoxLayout(cw)

        # --- project row (project selector lives in the main window, not Settings) ---
        prow = QtWidgets.QHBoxLayout()
        prow.addWidget(QtWidgets.QLabel("Project:"))
        self.combo_project = QtWidgets.QComboBox()
        self.combo_project.setToolTip(
            "Prism project. '(auto-detect)' = the project passed by Houdini when "
            "launched from the shelf, or derived from the chosen .hip. Otherwise pick "
            "a project (folders with 00_Pipeline under I:/) or Browse a pipeline.json."
        )
        self.combo_project.setMinimumWidth(300)
        self._fill_projects_combo()
        self.combo_project.currentIndexChanged.connect(self._on_project_combo_changed)
        prow.addWidget(self.combo_project)
        self.lbl_project = QtWidgets.QLabel("")
        self.lbl_project.setStyleSheet("color: gray;")
        prow.addWidget(self.lbl_project, 1)
        lay.addLayout(prow)

        # --- scene row ---
        bar = QtWidgets.QHBoxLayout()
        bar.addWidget(QtWidgets.QLabel("Scene (.hip):"))
        self.ed_hip = QtWidgets.QLineEdit(self.last_hip)
        self.ed_hip.setToolTip("The cfx .hip scene to inspect / re-cache from.")
        self.ed_hip.textChanged.connect(self._on_hip_changed)
        bar.addWidget(self.ed_hip, 1)
        b_proj = QtWidgets.QPushButton("Choose scene...")
        b_proj.setToolTip(
            "Pick a scene from the selected Prism project (seq / shot / dept / task)."
        )
        b_proj.clicked.connect(self._choose_scene)
        bar.addWidget(b_proj)
        b_hip = QtWidgets.QPushButton("Browse...")
        b_hip.setToolTip("Pick a .hip anywhere on the filesystem.")
        b_hip.clicked.connect(self._pick_hip)
        bar.addWidget(b_hip)
        b_set = QtWidgets.QPushButton("Settings...")
        b_set.setToolTip("hython path, node convention, reset (persisted).")
        b_set.clicked.connect(self._open_settings)
        bar.addWidget(b_set)
        lay.addLayout(bar)

        # --- layer + actions row ---
        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("Tracked layer:"))
        self.combo_layer = QtWidgets.QComboBox()
        self.combo_layer.setToolTip(
            "The USD layer whose version decides if a shot is outdated.\n"
            "Filled from the project's departments (pipeline.json)."
        )
        self.combo_layer.setMinimumWidth(220)
        self.combo_layer.currentIndexChanged.connect(self._on_layer_changed)
        top.addWidget(self.combo_layer)
        self.b_reload = QtWidgets.QPushButton("Reload (fast)")
        self.b_reload.setToolTip(
            "Re-check the version gaps by reading the DISK only (no Houdini, instant).\n"
            "Uses the last known state of the scene's nodes + scans the latest versions.\n"
            "Doesn't see node changes made in Houdini since -> use 'Load Scene (slow)'."
        )
        self.b_reload.clicked.connect(self._fast_reload)
        self.b_load = QtWidgets.QPushButton("Load Scene (slow)")
        self.b_load.setToolTip(
            "Load the scene in hython and read each shot's state — ground truth,\n"
            "but takes a while. Needed after the nodes changed in Houdini."
        )
        self.b_load.clicked.connect(self.load_scene)
        self.b_check = QtWidgets.QPushButton("Check outdated")
        self.b_check.setToolTip("Tick every shot flagged OUTDATED.")
        self.b_check.clicked.connect(self._check_outdated)
        top.addWidget(self.b_reload)
        top.addWidget(self.b_load)
        top.addWidget(self.b_check)
        top.addSpacing(16)
        self.lbl_mode = QtWidgets.QLabel("")
        self.lbl_mode.setToolTip(
            "How the displayed state was obtained:\n"
            "- verified (Houdini): loaded the scene, ground truth.\n"
            "- preview (cache): instant from the shared json, versions scanned from "
            "disk. 'uncertain' = scene re-saved since; 'obsolete' = a newer scene "
            "version exists -> Load Scene to be sure."
        )
        top.addWidget(self.lbl_mode)
        top.addStretch(1)
        lay.addLayout(top)

        # --- table (clic-glisse pour cocher/decocher plusieurs shots) ---
        self.table = CheckDragTableWidget(0, 6)
        self._set_headers()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.itemChanged.connect(self._update_apply_count)
        self.table.cellClicked.connect(self._on_cell_clicked)
        # partie HAUTE du splitter : table + bouton recache
        top_w = QtWidgets.QWidget()
        top_lay = QtWidgets.QVBoxLayout(top_w)
        top_lay.setContentsMargins(0, 0, 0, 0)
        top_lay.addWidget(self.table, 1)

        act = QtWidgets.QHBoxLayout()
        act.addStretch(1)
        self.b_apply = QtWidgets.QPushButton(APPLY_LABEL)
        self.b_apply.setToolTip(
            "For each ticked shot: bump the import to the latest version, re-cache,\n"
            "then version-up the scene in Prism.\n"
            "Lighting shots also get RE-RENDERED on the farm (their ticked layers)."
        )
        bf = self.b_apply.font()
        bf.setPointSize(max(11, bf.pointSize() + 2))
        bf.setBold(True)
        self.b_apply.setFont(bf)
        self.b_apply.setMinimumHeight(38)
        self.b_apply.setMinimumWidth(320)
        self.b_apply.clicked.connect(self.recache_selected)
        act.addWidget(self.b_apply)
        act.addStretch(1)  # stretch des DEUX cotes -> bouton CENTRE
        top_lay.addLayout(act)

        # --- console (REDIMENSIONNABLE : tire la poignee du splitter pour l'agrandir) ---
        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(8000)
        self.log.setMinimumHeight(140)
        f = QtGui.QFont("Consolas", 10)
        f.setStyleHint(QtGui.QFont.Monospace)
        self.log.setFont(f)
        self.log.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)

        self.split = QtWidgets.QSplitter(Qt.Vertical)
        self.split.addWidget(top_w)
        self.split.addWidget(self.log)
        self.split.setChildrenCollapsible(False)
        self.split.setStretchFactor(0, 3)
        self.split.setStretchFactor(1, 2)
        self.split.setSizes([520, 340])
        lay.addWidget(self.split, 1)

        self.status = self.statusBar()
        self.progress = QtWidgets.QProgressBar()
        self.progress.setMaximumWidth(220)
        self.progress.setTextVisible(True)
        self.progress.hide()
        self.status.addPermanentWidget(self.progress)
        self.status.showMessage(
            "Ready. Pick a .hip, then 'Load Scene (slow)' — or 'Reload (fast)' if it "
            "was already loaded once."
        )

    def _set_headers(self):
        layer = self._layer_display_name()
        labels = ["Shot", layer, "State", "SOP caches", "Renders", "Cache node"]
        tips = [
            "Prism shot (sequence/shot), resolved from the cache output",
            "Tracked-layer version: consumed -> latest (drives OUTDATED). "
            "Pick '%s' in the dropdown to follow the shot container." % STACK_LABEL,
            "OUTDATED / up to date / n/a / ERROR",
            "FX only: SOP caches re-simulated before publish (checked/total). "
            "Click to choose which caches to re-sim. Blank = cfx (no SOP chain).",
            "Lighting only: layers (render executions) rendered on the FARM when the "
            "shot is ticked (checked/total). Ticking the shot = re-cache THEN render "
            "these layers. Click to choose which layers; default = enabled on the node. "
            "Blank = no render node on this shot.",
            "The prism::lop_filecache node that will be re-cached",
        ]
        self.table.setHorizontalHeaderLabels(labels)
        for i, tip in enumerate(tips):
            self.table.horizontalHeaderItem(i).setToolTip(tip)

    # -------------------------------------------------------------- helpers
    def _pick_hip(self):
        start = os.path.dirname(self.ed_hip.text()) or ""
        p, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "cfx scene (.hip)", start, "Houdini (*.hip *.hipnc *.hiplc)"
        )
        if p:
            self.ed_hip.setText(p)

    @staticmethod
    def _is_prism_shots(shots):
        """Vrai 'Shots' Prism : dossier nomme 'Shots' dont le parent est '03_Production',
        OU dont le projet (parent du parent) contient 00_Pipeline/pipeline.json. Evite de
        detourner un dossier 'Shots' quelconque (ex archive) -> picker peuple mais faux."""
        if not shots or not os.path.isdir(shots) or os.path.basename(shots) != "Shots":
            return False
        parent = os.path.dirname(shots)
        if os.path.basename(parent) == "03_Production":
            return True
        proj = os.path.dirname(parent)
        return os.path.isfile(os.path.join(proj, "00_Pipeline", "pipeline.json"))

    @staticmethod
    def _find_shots_up(path):
        """Remonte depuis `path` jusqu'au 1er dossier 'Shots' qui est un VRAI Shots Prism
        (voir _is_prism_shots). '' si aucun (un 'Shots' non-Prism ne compte pas)."""
        p = path
        while p:
            if os.path.basename(p) == "Shots" and Main._is_prism_shots(p):
                return p
            nxt = os.path.dirname(p)
            if nxt == p:
                return ""
            p = nxt
        return ""

    @staticmethod
    def _resolve_shots_root(d):
        """Depuis un dossier CHOISI, localise le 'Shots' Prism : le dossier lui-meme,
        <d>/03_Production/Shots, <d>/Shots, ou en remontant (cas ou l'artiste a pointe
        un dossier de scene profond). '' si rien de coherent."""
        if not d or not os.path.isdir(d):
            return ""
        if Main._is_prism_shots(d):
            return d
        for sub in (
            os.path.join(d, "03_Production", "Shots"),
            os.path.join(d, "Shots"),
        ):
            if Main._is_prism_shots(sub):
                return sub
        return Main._find_shots_up(d)

    def _shots_root(self):
        """<project>/03_Production/Shots, depuis le pipeline.json ou un hip connu."""
        prj = self._project()
        if prj and os.path.isfile(prj):  # pipeline.json (pas un simple nom de projet)
            root = os.path.dirname(os.path.dirname(prj))
            cand = os.path.join(root, "03_Production", "Shots")
            if os.path.isdir(cand):
                return cand
        for start in (self.ed_hip.text().strip(), self.settings.value("last_hip", "")):
            r = self._find_shots_up(start)
            if r:
                return r
        # dernier recours : le shots_root memorise -- mais seulement s'il est encore un
        # VRAI Shots Prism (evite d'ouvrir le picker sur un projet obsolete/errone).
        stored = self.settings.value("shots_root", "")
        return stored if self._is_prism_shots(stored) else ""

    def _choose_scene(self):
        """Choisit une scene DANS le projet Prism selectionne (cascade seq/shot/dept/
        task). N'ouvre JAMAIS l'explorateur Windows (c'est le role de 'Browse...') :
        si aucun projet n'est selectionne/detecte, on le dit clairement."""
        root = self._shots_root()
        if not root or not os.path.isdir(root):
            QtWidgets.QMessageBox.information(
                self,
                "No project",
                "No project selected/detected.\n\nPick a project in the 'Project' "
                "dropdown at the top first — or use 'Browse...' to open a .hip directly.",
            )
            return
        self.settings.setValue("shots_root", root)
        dlg = ProjectPicker(self, root, current=self.ed_hip.text().strip())
        ok = dlg.exec() if hasattr(dlg, "exec") else dlg.exec_()
        if ok and dlg.selected_path():
            self.ed_hip.setText(dlg.selected_path())

    # ------------------------------------------------------ project selector
    def _fill_projects_combo(self):
        """Remplit le dropdown Projet : (auto-detect) + projets Prism sous I:/ +
        Browse. Pre-selectionne l'override courant."""
        self.combo_project.blockSignals(True)
        self.combo_project.clear()
        self.combo_project.addItem("(auto-detect)", "")
        cur = self.cfg.get("project_override", "")
        sel = 0
        for name, cfgpath in list_prism_projects(self.cfg.get("projects_root", "I:/")):
            self.combo_project.addItem(name, cfgpath)
            if os.path.normpath(cfgpath) == os.path.normpath(cur or "\0"):
                sel = self.combo_project.count() - 1
        if cur and os.path.isfile(cur) and sel == 0:  # override hors I:/ -> le montrer
            self.combo_project.addItem(project_name_of(cur), cur)
            sel = self.combo_project.count() - 1
        self.combo_project.addItem("Browse for pipeline.json...", "__browse__")
        self.combo_project.setCurrentIndex(sel)
        self.combo_project.blockSignals(False)

    def _on_project_combo_changed(self, idx):
        data = self.combo_project.itemData(idx)
        if data == "__browse__":
            p, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "pipeline.json",
                self.cfg.get("projects_root", "I:/"),
                "Prism project (pipeline.json)",
            )
            if p and os.path.isfile(p):
                at = self.combo_project.count() - 1  # avant 'Browse...'
                self.combo_project.blockSignals(True)
                self.combo_project.insertItem(at, project_name_of(p), p)
                self.combo_project.setCurrentIndex(at)
                self.combo_project.blockSignals(False)
                data = p
            else:  # annule -> revenir a l'override courant
                self._fill_projects_combo()
                return
        self.cfg["project_override"] = "" if data in ("", None) else data
        self._save_settings()
        self._on_hip_changed()

    def _project(self):
        """Chemin du pipeline.json du projet Prism. Priorite :
        1) override explicite (dropdown Projet de la fenetre) s'il pointe un fichier ;
        2) projet passe par Houdini au lancement (env LOP_UPDATE_CACHE_PROJECT) ;
        3) derive depuis le .hip (remontee jusqu'a 00_Pipeline/pipeline.json).
        Un simple nom de projet n'est jamais retourne (casserait --project)."""
        override = self.cfg.get("project_override", "")
        if override and os.path.isfile(override):
            return override
        env = os.environ.get(ENV_PROJECT, "")
        if env and os.path.isfile(env):
            return env
        return derive_project(self.ed_hip.text().strip())

    def _on_hip_changed(self):
        """Refresh apres changement de scene/projet : label projet + dropdown layer."""
        # scene differente -> le json partage sera recharge au prochain acces
        self._fx_store = None
        self._fx_selection = {}
        self._render_selection = {}
        prj = self._project()
        auto = not (
            self.cfg.get("project_override", "")
            and os.path.isfile(self.cfg["project_override"])
        )
        c = theme_colors(self)
        if prj:
            tag = "auto -> %s" % project_name_of(prj) if auto else project_name_of(prj)
            self.lbl_project.setText(tag)
            self.lbl_project.setStyleSheet("color: %s;" % c["gray"])
            self.lbl_project.setToolTip(prj)
        else:
            self.lbl_project.setText("no project selected/detected")
            self.lbl_project.setStyleSheet("color: %s;" % c["orange"])
            self.lbl_project.setToolTip("")
        self._refresh_layers()
        self._maybe_preview()  # affichage instantane depuis le json si dispo

    def _layers_in_data(self):
        """[(libelle, cle)] des layers REELLEMENT presents dans la scene chargee (union
        des cles `layers` de tous les shots).

        On ne se sert plus de pipeline.json (usd.departmentOrder) comme source : il
        liste tous les departements du projet, y compris ceux qu'aucun shot n'utilise
        -> dropdown verbeux et trompeur. Ici, ce qui est propose EXISTE.
        'USD' est le produit CONTAINER du shot : c'est le STACK, on l'affiche en clair
        et en premier (suivre le stack = "quelque chose a bouge dans le shot")."""
        names = set()
        for d in self._data or []:
            names.update((d.get("layers") or {}).keys())
        if not names:
            return []
        out = []
        if STACK_LAYER in names:
            out.append((STACK_LABEL, STACK_LAYER))
            names.discard(STACK_LAYER)
        for n in sorted(names):
            pretty = n.replace("_layer_", "").replace("_master", "") or n
            out.append(("%s  (%s)" % (pretty.capitalize(), n), n))
        return out

    def _refresh_layers(self):
        """Remplit le dropdown depuis les layers de la scene chargee ; a defaut (aucune
        scene chargee encore) depuis pipeline.json, pour avoir quelque chose a proposer."""
        depts = self._layers_in_data() or read_departments(self._project())
        self._departments = depts
        cur = self.cfg.get("tracked_layer", "_layer_anm_master")
        self.combo_layer.blockSignals(True)
        self.combo_layer.clear()
        idx = 0
        if depts:
            for i, (name, layer) in enumerate(depts):
                # les libelles de _layers_in_data sont deja finis ; seuls ceux de
                # read_departments (repli sans scene chargee) sont a decorer
                ready = "(" in name or name == STACK_LABEL
                self.combo_layer.addItem(
                    name if ready else "%s  (%s)" % (name, layer), layer
                )
                if layer == cur:
                    idx = i
        else:
            self.combo_layer.addItem(cur, cur)
        self.combo_layer.setCurrentIndex(idx)
        self.combo_layer.blockSignals(False)
        # keep cfg consistent with what's shown
        data = self.combo_layer.currentData()
        if data:
            self.cfg["tracked_layer"] = data
        self._set_headers()

    def _on_layer_changed(self):
        layer = self.combo_layer.currentData()
        if layer:
            self.cfg["tracked_layer"] = layer
            self._save_settings()
            # partage le layer tracke pour CETTE scene (json a cote du hip)
            if self._hip_sidecar_path():
                self._save_hip_store()
            self._set_headers()
            # the engine sends ALL layers -> re-render instantly, no scene reload
            if self._data:
                self._populate(self._data, preserve=True)
                self.status.showMessage(
                    "Layer switched to %s (no reload needed)."
                    % self._layer_display_name()
                )

    def _apply_saved_layer(self):
        """Applique le layer tracke du json partage (si present et connu du combo),
        sans recharger la scene ni re-populer (fait juste apres)."""
        self._ensure_store()
        layer = self._fx_store.get("tracked_layer", "")
        if not layer or layer == self.cfg.get("tracked_layer"):
            return
        i = self.combo_layer.findData(layer)
        self.combo_layer.blockSignals(True)
        if i >= 0:
            self.combo_layer.setCurrentIndex(i)
        self.combo_layer.blockSignals(False)
        self.cfg["tracked_layer"] = layer
        self._set_headers()

    def _layer_display_name(self):
        layer = self.cfg.get("tracked_layer", "_layer_anm_master")
        if layer == STACK_LAYER:
            return STACK_LABEL
        for name, lay in self._departments:
            if lay == layer:
                return name.split("  (")[0]
        return layer.replace("_layer_", "").replace("_master", "") or "Layer"

    def _open_settings(self):
        dlg = SettingsDialog(self, dict(self.cfg))
        ok = dlg.exec() if hasattr(dlg, "exec") else dlg.exec_()
        if getattr(dlg, "reset_requested", False):
            self._reset_local_settings()
            return
        if ok:
            self.cfg.update(dlg.values())
            self.cfg["hython"] = detect_hython(self.cfg.get("hython"))
            self._save_settings()
            self._on_hip_changed()

    def _reset_local_settings(self):
        """Efface TOUTES les prefs QSettings (scenes, projet, selections SOP, hython...)
        et recharge les defauts. Repart d'une machine 'propre'."""
        self.settings.clear()
        self.settings.sync()
        self._fx_selection = {}
        self._render_selection = {}
        self._fx_store = None  # le json partage (a cote du hip) N'est PAS efface
        self._data = []
        self.table.setRowCount(0)
        self._load_settings()  # QSettings vide -> defauts (+ env Houdini si present)
        self.ed_hip.blockSignals(True)
        self.ed_hip.setText(self.last_hip)
        self.ed_hip.blockSignals(False)
        self._fill_projects_combo()  # combo projet -> (auto-detect)
        self._on_hip_changed()
        self.status.showMessage("Local settings reset.")

    # -------------------------------------------------------------- process
    def _busy(self, on, msg=""):
        # grey out inputs while hython runs (esp. long FX re-sims) -> clearly "computing".
        # The window stays alive (async QProcess) so the artist keeps working in Houdini.
        for b in (self.b_reload, self.b_load, self.b_check, self.b_apply):
            b.setEnabled(not on)
        self.table.setEnabled(not on)
        self.combo_layer.setEnabled(not on)
        if msg:
            self.status.showMessage(msg)

    # ------------------------------------------------- feedback "ca calcule"
    def _tick(self):
        """Toutes les 200 ms pendant un run : spinner + chrono + phase courante, EN BAS.
        Un run peut durer des minutes sans rien ecrire (cook USD) -> sans ca, l'UI a
        l'air figee."""
        # Le chrono ne doit JAMAIS survivre a son run : si le signal `finished` n'atteint
        # pas l'UI (process tue, crash), le ticker continuerait d'accumuler pendant des
        # heures et de repeindre la statusbar 5x/s avec un temps delirant, toujours la
        # meme phase -> ca ressemble a un freeze. On s'arrete des qu'il n'y a plus de
        # process vivant.
        if self._t0 is None or self.proc is None:
            was_running = self._t0 is not None
            self._stop_ticker()
            if was_running:  # ticker fantome : on ne laisse pas un faux chrono affiche
                self.status.showMessage("Ready.")
            return
        self._spin = (self._spin + 1) % len(SPINNER)
        el = _fmt_elapsed(time.time() - self._t0)
        self.status.showMessage(
            "%s  %s  ·  %s" % (SPINNER[self._spin], self._phase or "Working…", el)
        )
        # le chrono va AUSSI dans la barre (visible meme si la statusbar est masquee)
        base = getattr(self, "_prog_shot", "") or ""
        self.progress.setFormat(("%s · %s" % (base, el)) if base else el)

    def _start_ticker(self, phase):
        self._phase = phase
        self._t0 = time.time()
        self._spin = 0
        self._ticker.start()
        self._tick()

    def _stop_ticker(self):
        self._ticker.stop()
        self._t0 = None
        self._phase = ""

    def _update_phase(self, text):
        """Detecte la phase courante depuis les lignes du moteur (voir PHASES)."""
        for line in text.split("\n"):
            for needle, label in PHASES:
                if needle in line:
                    self._phase = label
                    break

    def _engine_args(self):
        """Engine flags from the hip + settings (no config.json)."""
        args = [
            ENGINE,
            "--hip",
            self.ed_hip.text().strip(),
            "--project",
            self._project(),
        ]
        for key, flag in SETTING_TO_FLAG.items():
            args += [flag, str(self.cfg.get(key, ""))]
        return args

    @staticmethod
    def _houdini_build(entry):
        """Numero de build d'un composant de chemin d'INSTALL Houdini (ex '596','729'),
        ou None si le chemin n'est pas une install Houdini. Marche pour la forme longue
        ('Houdini 21.0.729') ET la forme courte 8.3 ('HOUDIN~1.729'). Ne matche PAS le
        dossier 'Houdini' de Prism (pas de numero accole)."""
        for comp in entry.replace("/", "\\").lower().split("\\"):
            if comp.startswith("houdini") or comp.startswith("houdin~"):
                nums = re.findall(r"\d+", comp)
                if nums:
                    return nums[-1]  # le build = dernier nombre du composant
        return None

    def _houdini_env(self, hy):
        """Environnement d'execution pour hython. Force la version du hython CHOISI et
        PURGE toute AUTRE install Houdini de PATH / PYTHONPATH / HOUDINI_PATH.

        Sinon, sur un PC ou une 2e version est installee (ex 21.0.729), son env fuit
        dans notre hython (ex 21.0.596) : `import hou` charge le _hou.pyd de l'autre
        version contre un python311.dll different -> SEGFAULT. On filtre par NUMERO DE
        BUILD (robuste aux chemins courts 8.3 type HOUDIN~1.729 vus dans la traceback),
        on epingle HFS + bin de la version choisie."""
        env = QProcessEnvironment.systemEnvironment()
        hfs = os.path.dirname(
            os.path.dirname(hy)
        )  # <root> depuis <root>\bin\hython.exe
        mine = self._houdini_build(hfs)

        def _keep(entry):
            b = self._houdini_build(entry)
            # b None -> pas une install Houdini (Prism, systeme...) : on garde.
            # sinon on ne garde que le meme build que le hython choisi.
            return b is None or mine is None or b == mine

        for var in ("PATH", "PYTHONPATH", "HOUDINI_PATH"):
            val = env.value(var, "")
            if val:
                kept = [p for p in val.split(os.pathsep) if p and _keep(p)]
                env.insert(var, os.pathsep.join(kept))
        # PYTHONHOME d'une autre install pointerait le mauvais python311 -> hython gere le sien
        env.remove("PYTHONHOME")
        env.insert("HFS", hfs)  # la bonne version fait autorite
        env.insert(
            "PATH", os.path.join(hfs, "bin") + os.pathsep + env.value("PATH", "")
        )
        return env

    def _start(self, mode, extra_args):
        if self.proc is not None:
            return
        hy = self.cfg.get("hython", "")
        hip = self.ed_hip.text().strip()
        if not hy or not os.path.exists(hy):
            QtWidgets.QMessageBox.warning(
                self, "hython", "hython not found (see Settings):\n%s" % hy
            )
            return
        if not hip or not os.path.exists(hip):
            QtWidgets.QMessageBox.warning(self, "Scene", "No .hip found:\n%s" % hip)
            return
        if not self._project():
            QtWidgets.QMessageBox.warning(
                self, "Project", "Prism project not found from this .hip."
            )
            return
        self._save_settings()
        self._buf = ""
        self._linebuf = ""
        self._in_status = False
        self._mode = mode
        args = self._engine_args() + extra_args
        self.log.appendPlainText("\n$ %s %s\n" % (hy, " ".join(args)))
        self.proc = QProcess(self)
        self.proc.setProcessEnvironment(self._houdini_env(hy))
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._on_out)
        self.proc.finished.connect(self._on_finished)
        self.proc.start(hy, args)
        self.progress.setRange(0, 0)  # indeterminate while the scene loads
        self.progress.show()
        self._prog_shot = ""
        self._busy(True)
        self._start_ticker("Starting Houdini…")

    def _on_out(self):
        data = bytes(self.proc.readAllStandardOutput()).decode("utf-8", "replace")
        # canal COMPLET (parsing des marqueurs) -- NE PAS filtrer ici.
        # /!\ On BORNE ce buffer : un run long crache des dizaines de Mo (sortie verbeuse
        # de Prism a chaque shot) et un `+=` sur une chaine geante est O(n^2) -> l'UI se
        # met a stalder de plus en plus, jusqu'a paraitre gelee. Les marqueurs cherches
        # (STATUS_JSON, SAVED_SCENE) sont toujours en FIN de flux, donc garder la queue
        # suffit ; le seuil est tres au-dessus d'un bloc STATUS_JSON (~200 Ko a 20 shots).
        self._buf += data
        if len(self._buf) > _BUF_MAX:
            self._buf = self._buf[-_BUF_KEEP:]
        # progress markers emitted by the engine during apply
        for m in re.finditer(r">>>PROGRESS>>>(\d+)/(\d+)<<<", data):
            cur, total = int(m.group(1)), int(m.group(2))
            self.progress.setRange(0, total)
            self.progress.setValue(cur)
            self._prog_shot = "shot %d / %d" % (cur, total)
            self.progress.setFormat(self._prog_shot)
        # FX sub-progress : SOP caches re-simulated within the current shot
        for m in re.finditer(r">>>SUBPROGRESS>>>(\d+)/(\d+)<<<", data):
            self.progress.setFormat(
                "%s · sim %s/%s"
                % (getattr(self, "_prog_shot", "shot"), m.group(1), m.group(2))
            )
        visible = self._visible_lines(data)
        if visible:
            self._update_phase(visible)  # -> texte "ce qu'il se passe" en bas
            self.log.moveCursor(QtGui.QTextCursor.End)
            self.log.insertPlainText(visible)
            self.log.moveCursor(QtGui.QTextCursor.End)

    def _visible_lines(self, data):
        """Ne garde pour le log HUMAIN que le lisible : masque le gros bloc STATUS_JSON
        (un canal de DONNEES pour l'UI, pas fait pour etre lu) et les lignes de marqueurs
        `>>>...<<<`. Bufferise les lignes partielles (le stdout arrive en morceaux)."""
        self._linebuf += data
        parts = self._linebuf.split("\n")
        self._linebuf = parts.pop()  # derniere ligne incomplete -> on attend la suite
        out = []
        for line in parts:
            s = line.strip()
            if STATUS_START in s or RECORDS_START in s:
                self._in_status = True
                continue
            if STATUS_END in s or RECORDS_END in s:
                self._in_status = False
                continue
            if self._in_status or s.startswith(">>>"):
                continue  # bloc data ou marqueur (PROGRESS/SUBPROGRESS/SAVED_SCENE)
            out.append(line)
        return ("\n".join(out) + "\n") if out else ""

    def _on_finished(self, code, _status):
        self.log.appendPlainText("\n[exit %s]" % code)
        took = _fmt_elapsed(time.time() - self._t0) if self._t0 else ""
        mode = self._mode
        self.proc = None
        self._mode = None
        self._stop_ticker()
        self.progress.hide()
        self._busy(False)
        if mode == "apply":
            self._store_cache_records()
            self._pick_saved_scene()
        # both status and apply emit a status JSON block -> refresh the table
        self._parse_status(silent=(mode == "apply"))
        if mode == "apply":
            ok = code == 0
            self.log.appendPlainText(
                "[UI] ===== UPDATE %s (exit %s, %s) — state refreshed ====="
                % ("FINISHED" if ok else "FAILED", code, took)
            )
            self.status.showMessage(
                "%s Update %s in %s (exit %s). State refreshed."
                % ("✓" if ok else "✗", "done" if ok else "FAILED", took, code)
            )
        else:
            self.status.showMessage("Scene loaded in %s (ground truth)." % took)

    def _store_cache_records(self):
        """Ecrit dans le sidecar les releves emis par le moteur : pour chaque shot cache,
        ce qu'il a CONSOMME et ce qu'il a PUBLIE. C'est cette trace (et non l'etat de la
        scene) qui dira ensuite si le shot est perime -- indispensable avec le node
        usd_layer_stack, qui se resout toujours au dernier publish."""
        a = self._buf.find(RECORDS_START)
        b = self._buf.find(RECORDS_END)
        if a == -1 or b == -1 or b < a:
            return
        try:
            recs = json.loads(self._buf[a + len(RECORDS_START) : b])
        except Exception as ex:
            self.log.appendPlainText("\n[UI] cache records unreadable: %s" % ex)
            return
        if not isinstance(recs, dict) or not recs:
            return
        self._ensure_store()
        self._fx_store.setdefault("cached", {}).update(recs)
        self._save_hip_store()
        self.log.appendPlainText(
            "\n[UI] cache records saved for %d shot(s): %s"
            % (len(recs), ", ".join(sorted(recs)))
        )

    def _pick_saved_scene(self):
        """After apply, the engine version-ups the scene; point the UI at it."""
        a = self._buf.find(">>>SAVED_SCENE>>>")
        b = self._buf.find("<<<SAVED_SCENE<<<")
        if a == -1 or b == -1:
            return
        newp = self._buf[a + len(">>>SAVED_SCENE>>>") : b].strip()
        if newp and os.path.exists(newp):
            self.ed_hip.blockSignals(True)
            self.ed_hip.setText(newp)
            self.ed_hip.blockSignals(False)
            self._save_settings()
            self.log.appendPlainText("\n[UI] scene updated to: %s" % newp)

    # --------------------------------------------------------------- status
    def _parse_status(self, silent=False):
        s = self._buf.find(STATUS_START)
        e = self._buf.find(STATUS_END)
        if s == -1 or e == -1:
            # Aucun etat recu (scene sans node reconnu, run interrompu, moteur en
            # erreur...). On VIDE la table : sinon les lignes de la scene PRECEDENTE
            # restent affichees, badge "verified" compris, et se lisent comme un verdict
            # sur la scene courante -- un user a ainsi vu "tout est up to date" sur une
            # scene que l'outil n'avait meme pas analysee.
            self._data = []
            self._populating = True
            try:
                self.table.setRowCount(0)
            finally:
                self._populating = False
            self._set_badge("")
            self._update_apply_count()
            self.status.showMessage(
                "No state received for this scene — nothing was analysed (see the log)."
            )
            return
        raw = self._buf[s + len(STATUS_START) : e].strip()
        try:
            data = json.loads(raw)
        except Exception as ex:
            self.status.showMessage("Invalid JSON: %s" % ex)
            return
        data.sort(key=_shot_sort_key)  # ordre SQ>SH (SQ0010/SH0010, SH0020, ...)
        self._data = data  # cached -> instant re-render on layer switch
        # le dropdown se remplit de ce qui EXISTE dans cette scene (+ le Stack), pas de
        # la liste projet -> il faut le refaire maintenant que les donnees sont la
        self._refresh_layers()
        self._apply_saved_layer()  # layer tracke memorise pour cette scene (json partage)
        self._save_snapshot(data)  # snapshot verifie -> preview instantane plus tard
        self._previewed = self.ed_hip.text().strip()  # etat frais = pas de re-preview
        self._set_badge("verified")
        self._populate(data)
        if not silent:
            n_out = sum(1 for d in data if d.get("state") == "outdated")
            n_err = sum(1 for d in data if d.get("state") == "error")
            self.status.showMessage(
                "%d shots  -  %d outdated  -  %d error." % (len(data), n_out, n_err)
            )

    def _pair(self, a, b):
        if not a and not b:
            return ""
        if a == b:
            return a or b or ""
        return "%s -> %s" % (a or "?", b or "?")

    def _layer_entry(self, d):
        """Per-shot data of the currently selected layer (exact key, else substring)."""
        layers = d.get("layers") or {}
        layer = self.cfg.get("tracked_layer", "")
        if layer in layers:
            return layers[layer]
        for k, v in layers.items():
            if layer in k or k in layer:
                return v
        return None

    def _row_state(self, d):
        """State of a row for the selected layer, computed client-side."""
        if not d.get("import_node"):
            return "no_import"
        if d.get("state") == "error":
            return "error"
        layers = d.get("layers")
        if not layers:  # old payload without per-layer data
            return d.get("state", "error")
        ld = self._layer_entry(d)
        if ld is None or (ld.get("consumed") is None and ld.get("latest") is None):
            return "no_layer"
        return "outdated" if ld.get("stale") else "uptodate"

    def _populate(self, data, preserve=False):
        """Remplit la table. `preserve=True` = on garde les cases COCHEES a l'identique.

        _populate reconstruit toutes les lignes, donc chaque case repart de son defaut
        ("cochee si OUTDATED"). Sur un simple re-rendu (OK d'un dialogue, changement de
        layer, scan de fond), ca ecrasait la selection de l'artiste et cochait d'un coup
        tous les shots perimes. Les re-rendus passent donc preserve=True ; seules les
        VRAIES arrivees de donnees (Load Scene, preview, fin d'apply) repartent du
        defaut."""
        prev = {}
        if preserve:
            for r in range(self.table.rowCount()):
                it = self.table.item(r, 0)
                if it is not None:
                    prev[it.data(Qt.UserRole)] = it.checkState() == Qt.Checked
        self._populating = True
        try:
            self._set_headers()
            self.table.setRowCount(0)
            col = theme_colors(self)  # fonds adaptes au theme clair/sombre
            for d in data:
                r = self.table.rowCount()
                self.table.insertRow(r)
                state = self._row_state(d)
                ld = self._layer_entry(d) or {}

                warn = d.get("warn") or ""  # real issue -> ⚠
                note = d.get("note") or ""  # benign info -> tooltip only
                label = d.get("shot", "")
                if warn:
                    label += "  ⚠"  # warning marker (real issues only)
                it0 = QtWidgets.QTableWidgetItem(label)
                it0.setData(Qt.UserRole, d.get("id", ""))  # selection handle
                it0.setFlags(it0.flags() | Qt.ItemIsUserCheckable)
                was = prev.get(
                    d.get("id", "")
                )  # None si ligne inconnue (ou pas preserve)
                ticked = (state == "outdated") if was is None else was
                it0.setCheckState(Qt.Checked if ticked else Qt.Unchecked)
                pm = d.get("pair_method")
                pm_txt = ("import paired by %s" % pm) if pm else ""
                tip = "  |  ".join(t for t in (warn, note, pm_txt, d.get("error")) if t)
                if tip:
                    it0.setToolTip(tip)
                self.table.setItem(r, 0, it0)

                vals = [
                    self._pair(
                        ld.get("consumed") or d.get("consumed_version"),
                        ld.get("latest") or d.get("latest_version"),
                    ),
                    STATE_TEXT.get(state, state),
                    self._sop_summary(d),
                    self._render_summary(d),
                    d.get("cache_node") or "",
                ]
                for c, v in enumerate(vals, start=1):
                    cell = QtWidgets.QTableWidgetItem(str(v))
                    if c == 3 and d.get("fx_chain"):  # SOP caches cell -> clickable
                        cell.setToolTip("Click to choose which SOP caches to re-sim.")
                        cell.setForeground(QtGui.QColor(col["sop"]))
                    if c == 4 and d.get("renders"):  # Renders cell -> clickable
                        cell.setToolTip(
                            "Click to choose which renders to submit to the farm."
                        )
                        cell.setForeground(QtGui.QColor(col["sop"]))
                    self.table.setItem(r, c, cell)

                color = {
                    "outdated": col["bg_outdated"],
                    "error": col["bg_error"],
                    "no_layer": col["bg_gray"],
                    "no_record": col["bg_gray"],
                    "no_import": col["bg_gray"],
                }.get(state)
                if color:
                    for c in range(self.table.columnCount()):
                        self.table.item(r, c).setBackground(color)
            self.table.resizeColumnsToContents()
        finally:
            self._populating = False
        self._update_apply_count()

    # ------------------------------------------------------- FX SOP cache chain
    def _sop_summary(self, d):
        """Cellule 'SOP caches' : 'coches/total ▸' (FX), '' (cfx : pas de chaine),
        '- (locked?)' (FX mais caches internes inatteignables)."""
        chain = d.get("fx_chain") or []
        if not chain:
            return "- (locked?)" if d.get("fx_sopcreate") else ""
        checked = self._fx_sel_for(d)
        n = sum(1 for c in chain if c.get("rel") in checked)
        return "%d/%d  ▸" % (n, len(chain))

    def _render_layers_for(self, d):
        """Layers (executions) distincts des LOP_Render du shot : [{layer, enabled}].
        enabled = OU logique si un layer apparait dans plusieurs nodes."""
        seen = {}
        for rn in d.get("renders") or []:
            for e in rn.get("executions") or []:
                lyr = e.get("layer")
                if lyr is None:
                    continue
                if lyr not in seen:
                    seen[lyr] = {"layer": lyr, "enabled": bool(e.get("enabled"))}
                elif e.get("enabled"):
                    seen[lyr]["enabled"] = True
        return list(seen.values())

    def _render_summary(self, d):
        """Cellule 'Renders' : 'coches/total ▸' (layers a rendre / total), '' si le shot
        n'a pas de LOP_Render. Cocher le SHOT = re-cache + render ces layers."""
        layers = self._render_layers_for(d)
        if not layers:
            return ""
        sel = self._render_sel_for(d)
        n = sum(1 for lyr in layers if lyr["layer"] in sel)
        return "%d/%d  ▸" % (n, len(layers))

    def _scene_key(self):
        """Cle scene (basename sans extension ni version) : la selection suit les
        version-ups (SQ0020-SH0090_FX_v024.hip -> SQ0020-SH0090_FX)."""
        base = os.path.splitext(os.path.basename(self.ed_hip.text().strip()))[0]
        return re.sub(r"_v\d+", "", base) or base

    # --- persistance PARTAGEE : un json a cote du hip -> memes params pour tous ---
    def _hip_sidecar_path(self):
        """Chemin du json PARTAGE a cote du hip (par scene, sans version). '' si pas de
        hip valide. Etant sur I:/, tout artiste qui ouvre la scene a les memes params."""
        hip = self.ed_hip.text().strip()
        d = os.path.dirname(hip) if hip else ""
        if not d or not os.path.isdir(d):
            return ""
        return os.path.join(d, self._scene_key() + ".lopcache.json")

    _STORE_DEFAULTS = {
        "fx_unselected": {},
        "render_layers": {},  # layers a rendre par shot (override ; defaut = Enabled node)
        # releve par shot de ce que le dernier cache a consomme/publie -> SOURCE DE
        # VERITE de la peremption, agnostique au type de node d'import
        "cached": {},
        "tracked_layer": "",
        "status": [],  # snapshot du dernier status -> preview instantane sans Houdini
        "scene_version": None,  # version du .hip snapshote (fraicheur)
        "scene_mtime": None,  # mtime de ce .hip
        "saved_at": None,
    }

    def _ensure_store(self):
        """Charge le json partage a cote du hip (lazy) -> self._fx_store (snapshot +
        selections + fraicheur)."""
        if self._fx_store is not None:
            return
        store = {
            k: (v.copy() if isinstance(v, (dict, list)) else v)
            for k, v in self._STORE_DEFAULTS.items()
        }
        p = self._hip_sidecar_path()
        if p and os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for k in store:
                        if k in data:
                            store[k] = data[k]
            except Exception:
                pass
        self._fx_store = store

    def _save_hip_store(self):
        """Ecrit tout le json partage a cote du hip."""
        p = self._hip_sidecar_path()
        if not p:
            return
        self._ensure_store()
        self._fx_store["tracked_layer"] = self.cfg.get("tracked_layer", "")
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(self._fx_store, f, indent=2)
        except Exception as ex:
            self.log.appendPlainText("[UI] sidecar write failed: %s" % ex)

    def _save_snapshot(self, data):
        """Enregistre le snapshot complet (status verifie Houdini + fraicheur) dans le
        json partage -> reaffichage instantane au prochain acces, par n'importe qui."""
        self._ensure_store()
        hip = self.ed_hip.text().strip()
        self._fx_store["status"] = data
        self._fx_store["scene_version"] = preview.hip_version(hip)
        try:
            self._fx_store["scene_mtime"] = (
                os.path.getmtime(hip) if os.path.isfile(hip) else None
            )
        except Exception:
            self._fx_store["scene_mtime"] = None
        self._fx_store["saved_at"] = time.time()
        self._save_hip_store()

    # ------------------------------------------------- preview (sans Houdini)
    def _set_badge(self, kind):
        c = theme_colors(self)
        txt, key = {
            "verified": ("verified (Houdini)", "green"),
            "preview-verified": ("preview · verified", "green"),
            "preview-uncertain": ("preview · uncertain — reload to confirm", "orange"),
            "preview-obsolete": ("preview · newer scene exists — Load Scene", "red"),
            "preview-unknown": ("preview (cache)", "gray"),
        }.get(kind, ("", "gray"))
        self.lbl_mode.setText(txt)
        self.lbl_mode.setStyleSheet("color: %s; font-weight: bold;" % c[key])

    def _maybe_preview(self):
        """Preview instantane depuis le json au changement de scene (hors Houdini)."""
        hip = self.ed_hip.text().strip()
        if self.proc is not None or not os.path.isfile(hip) or hip == self._previewed:
            return
        self._ensure_store()
        if self._fx_store.get("status"):
            self._previewed = hip
            self._preview_scene()

    def _preview_scene(self, preserve=False):
        """Affiche instantanement l'etat du snapshot (0 Houdini) + fraicheur, puis
        scanne le disque en tache de fond pour rafraichir les gaps de version.

        `preserve=True` : on garde les cases cochees telles quelles (Reload sur la MEME
        scene). Un CHANGEMENT de scene repart du defaut ('cochee si outdated')."""
        self._ensure_store()
        snap = self._fx_store.get("status") or []
        if not snap:
            return
        hip = self.ed_hip.text().strip()
        fr = preview.freshness(
            hip, self._fx_store.get("scene_version"), self._fx_store.get("scene_mtime")
        )
        data = json.loads(json.dumps(snap))  # copie (le scan mute en place)
        data.sort(key=_shot_sort_key)
        self._data = data
        self._refresh_layers()  # dropdown = layers reellement presents (+ le stack)
        self._apply_saved_layer()
        self._populate(data, preserve=preserve)
        self._set_badge("preview-" + fr)
        self.status.showMessage(
            "Preview from cache (%s) — versions scanned from disk. "
            "'Load Scene (slow)' for ground truth." % fr
        )
        self._start_scan(data)

    def _newer_scene(self):
        """(chemin, version) d'une version .hip PLUS RECENTE que celle du champ, sinon
        None. Pur (pas d'UI) -> testable."""
        hip = self.ed_hip.text().strip()
        cur = preview.hip_version(hip)
        latest = preview.latest_hip_version(hip)
        if cur is None or latest is None or latest <= cur:
            return None
        path = preview.hip_at_version(hip, latest)
        return (path, latest) if path else None

    def _guard_newer_scene(self):
        """AVANT un apply : si une version plus recente existe, le moteur chargerait
        l'ANCIENNE scene (--hip = le champ) puis version-uperait par-dessus -> le travail
        fait entre les deux disparait de la nouvelle version. On previent, on propose de
        basculer sur la derniere. Retourne True si on peut continuer."""
        newer = self._newer_scene()
        if not newer:
            return True
        path, latest = newer
        cur_v = preview.hip_version(self.ed_hip.text().strip())
        box = QtWidgets.QMessageBox(self)
        box.setIcon(QtWidgets.QMessageBox.Warning)
        box.setWindowTitle("A newer scene exists")
        box.setText(
            "A newer version of this scene exists: <b>v%03d</b>.<br><br>"
            "You are about to update from <b>v%03d</b> and publish v%03d — everything "
            "saved in v%03d…v%03d would be <b>ignored</b>."
            % (latest, cur_v, latest + 1, cur_v + 1, latest)
        )
        box.setInformativeText("What do you want to do?")
        b_latest = box.addButton("Use latest (v%03d)" % latest, box.AcceptRole)
        b_anyway = box.addButton("Continue anyway", box.DestructiveRole)
        b_cancel = box.addButton("Cancel", box.RejectRole)
        box.setDefaultButton(b_latest)
        box.exec() if hasattr(box, "exec") else box.exec_()
        clicked = box.clickedButton()
        if clicked is b_cancel:
            return False
        if clicked is b_latest:
            # bascule le champ sans declencher la cascade de _on_hip_changed (le sidecar
            # est indexe sans la version -> selections conservees)
            self.ed_hip.blockSignals(True)
            self.ed_hip.setText(path)
            self.ed_hip.blockSignals(False)
            self._previewed = path
            self.log.appendPlainText("\n[UI] switched to the latest scene: %s" % path)
            self.status.showMessage("Switched to v%03d (latest)." % latest)
        elif clicked is b_anyway:
            self.log.appendPlainText(
                "\n[UI] WARNING: updating from v%03d while v%03d exists (user choice)."
                % (cur_v, latest)
            )
        return True

    def _fast_reload(self):
        """Bouton 'Reload (fast)' : re-check les ecarts de version en lisant le DISQUE
        seulement (0 Houdini, instantane). Repart du dernier etat connu des nodes
        (snapshot du sidecar) et re-scanne les dernieres versions publiees. Ne voit PAS
        un changement de nodes fait dans Houdini depuis -> 'Load Scene (slow)' pour ca."""
        if self.proc is not None:
            return
        hip = self.ed_hip.text().strip()
        if not hip or not os.path.isfile(hip):
            QtWidgets.QMessageBox.warning(self, "Scene", "No .hip found:\n%s" % hip)
            return
        self._ensure_store()
        if not self._fx_store.get("status"):
            QtWidgets.QMessageBox.information(
                self,
                "Reload (fast)",
                "No cached state for this scene yet.\n\n"
                "Run 'Load Scene (slow)' once — after that, 'Reload (fast)' re-checks "
                "the versions from disk instantly.",
            )
            return
        self._previewed = hip
        # meme scene : un reload ne doit RIEN decider a la place de l'artiste, sa
        # selection de shots reste telle quelle (seules les versions sont rafraichies)
        self._preview_scene(preserve=True)

    def _start_scan(self, data):
        if self._scan is not None:
            return
        self._ensure_store()
        self._scan = _ScanWorker(
            json.loads(json.dumps(data)), self._fx_store.get("cached") or {}
        )
        self._scan.done.connect(self._on_scan_done)
        self._scan.start()

    def _on_scan_done(self, data):
        self._scan = None
        if self.proc is not None:  # un Load Scene est parti entre-temps -> priorite
            return
        data.sort(key=_shot_sort_key)
        self._data = data
        # scan de fond : l'artiste a pu cocher pendant -> on ne rebat pas ses cases
        self._populate(data, preserve=True)

    def _fx_sel_for(self, d):
        """Set des 'rel' coches pour ce shot. Source = json partage (DECOCHES stockes ->
        un cache ajoute plus tard au setup est coche par defaut). Defaut = tout coche."""
        self._ensure_store()
        shot = d.get("shot", "")
        chain = d.get("fx_chain") or []
        all_rels = [c.get("rel") for c in chain]
        if shot not in self._fx_selection:
            unchecked = set(self._fx_store.get("fx_unselected", {}).get(shot, []))
            self._fx_selection[shot] = [r for r in all_rels if r not in unchecked]
        return set(self._fx_selection[shot])

    def _save_fx_sel(self, shot, checked_rels, all_rels, flush=True):
        self._ensure_store()
        checked = set(checked_rels)
        self._fx_selection[shot] = [r for r in all_rels if r in checked]
        unchecked = [r for r in all_rels if r not in checked]
        self._fx_store.setdefault("fx_unselected", {})[shot] = unchecked
        if flush:
            self._save_hip_store()

    def _render_sel_for(self, d):
        """Set des LAYERS a rendre pour ce shot. Override stocke dans le json partage
        (`render_layers`) ; si absent -> defaut = les layers actuellement Enabled sur le
        node (behavior 1). Cocher le SHOT rendra ces layers."""
        self._ensure_store()
        shot = d.get("shot", "")
        layers = self._render_layers_for(d)
        all_names = [lyr["layer"] for lyr in layers]
        if shot not in self._render_selection:
            override = self._fx_store.get("render_layers", {}).get(shot)
            if override is None:  # defaut = Enabled sur le node
                self._render_selection[shot] = [
                    lyr["layer"] for lyr in layers if lyr["enabled"]
                ]
            else:
                keep = set(override)
                self._render_selection[shot] = [n for n in all_names if n in keep]
        return set(self._render_selection[shot])

    def _save_render_sel(self, shot, checked_layers, all_names, flush=True):
        self._ensure_store()
        checked = set(checked_layers)
        keep = [n for n in all_names if n in checked]
        self._render_selection[shot] = keep
        self._fx_store.setdefault("render_layers", {})[shot] = keep
        if flush:
            self._save_hip_store()

    def _on_cell_clicked(self, row, col):
        if col not in (3, 4):
            return
        ident = self.table.item(row, 0).data(Qt.UserRole)
        d = next((x for x in self._data if x.get("id") == ident), None)
        if not d:
            return
        if col == 3 and d.get("fx_chain"):
            self._open_fx_dialog(d)
        elif col == 4 and self._render_layers_for(d):
            self._open_render_dialog(d)

    def _open_render_dialog(self, d):
        shot = d.get("shot", "")
        layers = self._render_layers_for(d)
        dlg = RenderPickerDialog(self, shot, layers, self._render_sel_for(d))
        ok = dlg.exec() if hasattr(dlg, "exec") else dlg.exec_()
        if not ok:
            return
        all_names = [lyr["layer"] for lyr in layers]
        self._save_render_sel(shot, dlg.checked_layers(), all_names)
        if dlg.apply_to_all():
            self._apply_render_sel_to_all(dlg.checked_layers())
        self._populate(self._data, preserve=True)  # refresh the summary cell

    def _apply_render_sel_to_all(self, checked_layers):
        """Propage la selection de layers a TOUS les shots ayant des renders, PAR NOM de
        layer (les layers sont communs aux shots)."""
        checked = set(checked_layers)
        for d in self._data:
            layers = self._render_layers_for(d)
            if not layers:
                continue
            all_names = [lyr["layer"] for lyr in layers]
            keep = [n for n in all_names if n in checked]
            self._save_render_sel(d.get("shot", ""), keep, all_names, flush=False)
        self._save_hip_store()

    def _build_render_plan(self, ids):
        """{cache_id: [{node, layers}]} pour les shots COCHES ayant des renders + au moins
        un layer selectionne. Cocher un shot lighting = re-cache PUIS render ces layers.
        Un shot dont tous les layers sont decoches -> absent (re-cache seul, pas de render)."""
        plan = {}
        idset = set(ids)
        for d in self._data:
            if d.get("id") not in idset:
                continue
            renders = d.get("renders") or []
            if not renders:
                continue
            sel = sorted(self._render_sel_for(d))
            if not sel:  # tout decoche -> re-cache seul, aucun render
                continue
            plan[d["id"]] = [{"node": rn.get("path"), "layers": sel} for rn in renders]
        return plan

    def _open_fx_dialog(self, d):
        shot = d.get("shot", "")
        chain = d.get("fx_chain") or []
        dlg = FxChainDialog(self, shot, chain, self._fx_sel_for(d))
        ok = dlg.exec() if hasattr(dlg, "exec") else dlg.exec_()
        if not ok:
            return
        all_rels = [c.get("rel") for c in chain]
        self._save_fx_sel(shot, dlg.checked_rels(), all_rels)
        if dlg.apply_to_all():
            self._apply_sel_to_all(chain, dlg.checked_rels())
        self._populate(self._data, preserve=True)  # refresh the summaries

    def _apply_sel_to_all(self, src_chain, src_checked_rels):
        """Propage la selection du shot source a TOUS les shots PAR NOM de cache (pas par
        position : l'ordre des caches differe selon les shots -> position = faux). Un
        cache DECOCHE dans la source est decoche partout (par nom) ; le reste est coche."""
        src_checked = set(src_checked_rels)
        unchecked_names = {
            c.get("name") for c in src_chain if c.get("rel") not in src_checked
        }
        for d in self._data:
            chain = d.get("fx_chain") or []
            if not chain:
                continue
            all_rels = [c.get("rel") for c in chain]
            checked = [
                c.get("rel") for c in chain if c.get("name") not in unchecked_names
            ]
            self._save_fx_sel(d.get("shot", ""), checked, all_rels, flush=False)
        self._save_hip_store()  # une seule ecriture pour tout le batch

    def _build_fx_plan(self, ids):
        """{cache_id: [chemins SOP coches, ordre topo]} pour les shots recaches ayant
        une chaine. [] pour un shot tout decoche -> republish seul."""
        plan = {}
        idset = set(ids)
        for d in self._data:
            if d.get("id") not in idset:
                continue
            chain = d.get("fx_chain") or []
            if not chain:
                continue
            checked = self._fx_sel_for(d)
            plan[d["id"]] = [c.get("path") for c in chain if c.get("rel") in checked]
        return plan

    def _check_outdated(self):
        for r in range(self.table.rowCount()):
            outdated = self.table.item(r, 2).text() == "OUTDATED"
            self.table.item(r, 0).setCheckState(
                Qt.Checked if outdated else Qt.Unchecked
            )
        self._update_apply_count()

    def _update_apply_count(self, *_args):
        """Show how many shots are ticked, right on the action button."""
        if self._populating:
            return
        n = len(self._selected()[0])
        self.b_apply.setText("%s (%d)" % (APPLY_LABEL, n) if n else APPLY_LABEL)

    def _selected(self):
        """Return (ids, labels) of the ticked rows."""
        ids, labels = [], []
        for r in range(self.table.rowCount()):
            it = self.table.item(r, 0)
            if it.checkState() == Qt.Checked:
                ids.append(it.data(Qt.UserRole) or it.text())
                labels.append(it.text())
        return ids, labels

    # -------------------------------------------------------------- actions
    def load_scene(self):
        self._start("status", ["--status"])

    def recache_selected(self):
        ids, labels = self._selected()
        if not ids:
            QtWidgets.QMessageBox.information(self, "Selection", "No shot ticked.")
            return
        # garde-fou AVANT tout : ne pas updater depuis une scene perimee (sinon le
        # version-up ecraserait le travail fait entre-temps)
        if not self._guard_newer_scene():
            return
        # FX: quels caches SOP re-simuler par shot (coches dans l'UI) -> plan json
        plan = self._build_fx_plan(ids)
        n_sop = sum(len(v) for v in plan.values())
        # Lighting: quels shots re-rendre a la ferme + leurs layers -> plan json
        rplan = self._build_render_plan(ids)
        n_render_shots = len(rplan)
        n_jobs = sum(len(v) for v in rplan.values())
        extra_msg = ""
        if plan:
            extra_msg += (
                "\n(FX: %d SOP cache(s) will be re-simulated first — this can "
                "be long; the window stays greyed while it computes.)" % n_sop
            )
        if rplan:
            extra_msg += (
                "\n(LIGHTING: %d shot(s) will be RE-RENDERED on the farm (Deadline, "
                "%d job(s)) with their selected layers, after the re-cache.)"
                % (n_render_shots, n_jobs)
            )
        msg = (
            "Update %d shot(s)?\n"
            "This publishes a NEW version and version-ups the scene:\n\n%s%s"
            % (len(ids), ", ".join(labels), extra_msg)
        )
        yes = QtWidgets.QMessageBox.StandardButton.Yes
        if QtWidgets.QMessageBox.question(self, "Confirm update", msg) != yes:
            return
        # cocher = intention explicite -> on cache TOUS les shots coches, meme ceux
        # deja a jour (--force ; sinon le moteur skippe les non-perimes).
        extra = ["--apply", "--force", "--shots"] + ids
        if plan:
            pf = os.path.join(tempfile.gettempdir(), "lop_update_cache_fx_plan.json")
            try:
                with open(pf, "w", encoding="utf-8") as fh:
                    json.dump(plan, fh)
                extra += ["--fx-plan", pf]
            except Exception as ex:
                self.log.appendPlainText("\n[UI] fx-plan write failed: %s" % ex)
        if rplan:
            rf = os.path.join(
                tempfile.gettempdir(), "lop_update_cache_render_plan.json"
            )
            try:
                with open(rf, "w", encoding="utf-8") as fh:
                    json.dump(rplan, fh)
                extra += ["--render-plan", rf]
            except Exception as ex:
                self.log.appendPlainText("\n[UI] render-plan write failed: %s" % ex)
        self._start("apply", extra)


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = Main()
    w.show()
    sys.exit(app.exec() if hasattr(app, "exec") else app.exec_())


if __name__ == "__main__":
    main()
