# -*- coding: utf-8 -*-
"""
cfx_recache_ui.py - Standalone picker for the cfx re-cache tool.

Everything is configured in the app (no config.json): the artist picks the .hip,
the Prism project is derived automatically, the tracked layer is chosen from a
dropdown filled from the project's pipeline.json, and other settings are
persisted via QSettings. This UI does NOT load Houdini itself: it runs
recache_cfx.py through hython as a subprocess (QProcess) to read shot state
(--status) and re-cache the selection (--apply).

The scene is picked in the left panel, always open (SceneBrowser), in 3 columns:
Sequence/Shot | Department | Task (one row per task = its latest version).

A Maya scene (.ma) switches the window to RIG mode: the table lists the rigs the
scene references (read from the .ma text, instant, no Maya), and the update runs
recache_maya.py through mayapy: swap the ticked rigs -> refuse if animation was lost
-> version-up (or leave the scene untouched) -> run the ticked Prism exports.
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

from lop_update_cache import maya_refs, preview

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "recache_cfx.py")
ENGINE_MAYA = os.path.join(HERE, "recache_maya.py")

# Type de scene : decide du moteur (hython / mayapy) et de ce que montre la fenetre.
HOUDINI_EXT = (".hip", ".hipnc", ".hiplc")
MAYA_EXT = (".ma", ".mb")  # .mb = binaire : illisible sans Maya, jamais propose
PICKER_EXT = HOUDINI_EXT + (".ma",)


def rig_label(rig_id):
    """Libelle d'un rig depuis son id 'asset|produit'. Le produit n'est montre que s'il
    n'est pas le 'Rigging' standard : un asset peut avoir un rig PAR VARIANT
    (Props/cutlery : Rigging ET Rigging_forkA, vu sur frederic_2603) -> sans le produit,
    deux lignes identiques."""
    asset, _, product = (rig_id or "?").partition("|")
    return asset if product in ("", "Rigging") else "%s · %s" % (asset, product)


def scene_kind(path):
    """'houdini' | 'maya' | '' selon l'extension de la scene."""
    ext = os.path.splitext(path or "")[1].lower()
    if ext in HOUDINI_EXT:
        return "houdini"
    if ext in MAYA_EXT:
        return "maya"
    return ""


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
# verdict du moteur Maya (cf recache_maya.emit_result)
MAYA_RESULT_START = ">>>MAYA_RESULT>>>"
MAYA_RESULT_END = "<<<MAYA_RESULT<<<"
MAYA_COMMENT = "auto update - lop_update_cache"

DEFAULT_SETTINGS = {
    "hython": r"C:\Program Files\Side Effects Software\Houdini 21.0.729\bin\hython.exe",
    "mayapy": r"C:\Program Files\Autodesk\Maya2025\bin\mayapy.exe",
    "stage_root": "/stage",
    "import_pattern": "{shot}",
    "cache_pattern": "cache_{shot}",
    "import_node_type": "prism::LOP_Import",
    "import_path_parm": "filepath",
    "tracked_layer": "_layer_anm_master",  # forme historique (1 layer), encore lue
    "tracked_layers": ["_layer_anm_master"],  # forme courante : plusieurs layers suivis
    "tracked_mode": "or",  # 'or' = un seul suffit ; 'and' = il faut qu'ils aient TOUS bouge
    # sauvegarde de la scene apres l'update : 'version_up' (defaut = comportement historique)
    # ou 'leave'. PAR UTILISATEUR (QSettings), JAMAIS dans le sidecar partage : sinon le
    # choix de l'un s'imposerait au suivant qui ouvre la scene.
    "save_mode": "version_up",
    "projects_root": "I:/",  # ou scanner les projets Prism (dossiers avec 00_Pipeline)
}


def as_layer_list(v):
    """Normalise une valeur de settings en liste de layers. QSettings ne rend pas
    fidelement une liste (str si 1 element) -> on accepte str, liste, None."""
    if isinstance(v, str):
        return [x.strip() for x in v.split(",") if x.strip()]
    if isinstance(v, (list, tuple)):
        return [str(x).strip() for x in v if str(x).strip()]
    return []


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
    # tracked layer(s) : PAS ici -- le flag est repetable, cf _engine_args
}

SETTING_HELP = {
    "hython": "Path to hython.exe used to run the engine.\n"
    "Auto-detected from your Houdini installs if left at a missing path.",
    "mayapy": "Path to mayapy.exe used to update the rigs of a Maya scene (.ma).\n"
    "Auto-detected from your Maya installs if left at a missing path.",
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
    # en retard MAIS epingle dans le usd_layer_stack : choix de l'artiste, l'outil ne
    # depingle pas (cf preview.mark_pins)
    "pinned": "pinned",
    "error": "ERROR",
}

# Le bouton d'action ne fait plus que "recacher" : cfx/fx = re-cache, lighting = re-cache
# + re-render sur la ferme. D'ou un libelle neutre.
APPLY_LABEL = "Update selected shots"
APPLY_LABEL_MAYA = "Update selected rigs"

# Mode de sauvegarde de la scene apres l'update (choisi PAR RUN, memorise PAR UTILISATEUR)
SAVE_VERSION_UP = "version_up"  # caches publies + version-up Prism de la scene
SAVE_LEAVE = "leave"  # caches publies, scene NON ecrite (--no-save)
SAVE_MODE_TEXT = {
    SAVE_VERSION_UP: "Publishes the caches and saves a new scene version.",
    SAVE_LEAVE: "Publishes the caches only. The scene file is not written, "
    "so nobody's version chain changes.",
}
# meme choix pour une scene Maya, mais ce qui est publie, ce sont ses EXPORTS
SAVE_MODE_TEXT_MAYA = {
    SAVE_VERSION_UP: "Updates the rigs, saves a new scene version, then runs the "
    "ticked exports.",
    SAVE_LEAVE: "Updates the rigs and runs the ticked exports. The scene file is not "
    "written, so nobody's version chain changes.",
}
SAVE_LEAVE_DRY_RUN = (
    "No export ticked: dry run. The rigs are swapped in memory and checked for lost "
    "animation, nothing is written."
)

# Animation "ca calcule" : sablier braille (police mono, largeur constante).
SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

# Bornes du buffer stdout (cf _on_out) : au-dela de _BUF_MAX on ne garde que la queue.
_BUF_MAX = 8 * 1024 * 1024
_BUF_KEEP = 4 * 1024 * 1024

# Ce que raconte le moteur -> phase lisible affichee EN BAS pendant le run.
# (motif dans la ligne de log, libelle) ; 1er match gagne, ordre = du + precis au + large.
PHASES = [
    # moteur Maya (recache_maya.py) -- avant les motifs Houdini : "Scene chargee dans
    # Maya" contient "Scene chargee", le plus precis doit gagner
    ("Demarrage de Prism dans Maya", "Starting Maya + Prism…"),
    (
        "Chargement de la scene dans Maya",
        "Loading the scene and its rigs in Maya (long)…",
    ),
    ("Scene chargee dans Maya", "Scene loaded — swapping the rigs…"),
    ("Swap des rigs", "Swapping the rigs…"),
    ("Verification de l'animation", "Checking that no animation was lost…"),
    ("Version-up de la scene", "Saving the new scene version (Prism)…"),
    ("Export Prism", "Exporting (Prism)…"),
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


PRISM_INTEGRATION = r"C:\ILLOGIC_APP\Prism\2.0.18\plugins\Houdini\Integration"


def hython_python_version(hython_path):
    """(major, minor) du python embarque, lu SANS lancer Houdini : la dll
    `<HFS>/bin/python3XX.dll`. /!\ le dossier `python3XX` de l'install MENT
    (Houdini 22.0.368 a un dossier 'python310' et tourne en python 3.13)."""
    for dll in glob.glob(os.path.join(os.path.dirname(hython_path), "python3*.dll")):
        m = re.search(r"python(\d)(\d+)\.dll$", os.path.basename(dll).lower())
        if m:
            return (int(m.group(1)), int(m.group(2)))
    return None


def prism_python_versions(integration=None):
    """Versions de python pour lesquelles Prism fournit une integration Houdini."""
    out = set()
    try:
        names = os.listdir(integration or PRISM_INTEGRATION)
    except Exception:
        return out
    for d in names:
        m = re.match(r"^python(\d+)\.(\d+)libs$", d)
        if m:
            out.add((int(m.group(1)), int(m.group(2))))
    return out


def detect_hython(configured):
    """Le hython configure s'il existe, sinon le plus recent QUE PRISM SAIT CHARGER.

    /!\ "le plus recent" tout court ne suffit pas : Houdini 22.0.368 tourne en python
    3.13, pour lequel Prism 2.0.18 n'a pas d'integration -> PrismInit plante
    (ModuleNotFoundError PySide2). Quand un poste desinstalle sa version de reference,
    on tombait dessus en silence. On ne retient donc que les installs dont le python
    embarque a une integration Prism ; a defaut (Prism introuvable) on garde l'ancien
    comportement plutot que de ne rien proposer.
    'Plus recent' = tri NUMERIQUE de la version (pas lexical : 21.0.100 > 21.0.99)."""
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

    ok = prism_python_versions()
    usable = [p for p in found if hython_python_version(p) in ok] if ok else []
    return max(usable or found, key=_vkey)


def detect_mayapy(configured):
    """Le mayapy configure s'il existe, sinon celui du Maya le plus recent installe
    (tri numerique de l'annee : Maya2025 > Maya2024)."""
    if configured and os.path.exists(configured):
        return configured
    found = glob.glob(r"C:\Program Files\Autodesk\Maya*\bin\mayapy.exe")
    if not found:
        return configured or ""

    def _ykey(p):
        m = re.search(r"Maya(\d+)", p)
        return int(m.group(1)) if m else 0

    return max(found, key=_ykey)


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

        self.ed_mayapy = QtWidgets.QLineEdit(values.get("mayapy", ""))
        b_my = QtWidgets.QPushButton("...")
        b_my.clicked.connect(self._pick_mayapy)
        row_my = QtWidgets.QHBoxLayout()
        row_my.addWidget(self.ed_mayapy)
        row_my.addWidget(b_my)
        self._add_row(form, "mayapy:", row_my, SETTING_HELP["mayapy"])

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

    def _pick_mayapy(self):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "mayapy.exe", "", "mayapy (mayapy.exe)"
        )
        if p:
            self.ed_mayapy.setText(p)

    def values(self):
        return {
            "hython": self.ed_hython.text().strip(),
            "mayapy": self.ed_mayapy.text().strip(),
            "stage_root": self.ed_stage.text().strip() or "/stage",
            "import_pattern": self.ed_imp_pat.text().strip() or "{shot}",
            "cache_pattern": self.ed_cache_pat.text().strip() or "cache_{shot}",
            "import_node_type": self.ed_imp_type.text().strip() or "prism::LOP_Import",
            "import_path_parm": self.ed_path_parm.text().strip() or "filepath",
        }


class LayerFilterDialog(QtWidgets.QDialog):
    """ "Advanced sorting" : suivre PLUSIEURS layers a la fois, en ANY (OU) ou ALL (ET).

    Le cas courant (un seul layer) reste dans le dropdown de la fenetre : ce dialogue
    n'existe que pour le cas avance, il ne doit donc rien encombrer par defaut."""

    def __init__(self, parent, departments, selected, mode):
        super().__init__(parent)
        self.setWindowTitle("Advanced sorting - tracked layers")
        self.resize(420, 520)
        sel = set(selected or [])
        v = QtWidgets.QVBoxLayout(self)
        v.addWidget(
            QtWidgets.QLabel(
                "A shot is OUTDATED when the ticked layers moved. "
                "A layer this shot doesn't consume is ignored for that shot."
            )
        )
        row = QtWidgets.QHBoxLayout()
        self.rb_or = QtWidgets.QRadioButton("ANY of them  (OR)")
        self.rb_and = QtWidgets.QRadioButton("ALL of them  (AND)")
        self.rb_or.setToolTip("Outdated as soon as ONE of the ticked layers moved.")
        self.rb_and.setToolTip("Outdated only when they ALL moved.")
        (self.rb_and if mode == "and" else self.rb_or).setChecked(True)
        row.addWidget(self.rb_or)
        row.addWidget(self.rb_and)
        row.addStretch(1)
        v.addLayout(row)
        self.listw = QtWidgets.QListWidget()
        for name, layer in departments or []:
            ready = "(" in name or name == STACK_LABEL
            it = QtWidgets.QListWidgetItem(
                name if ready else "%s  (%s)" % (name, layer)
            )
            it.setData(Qt.UserRole, layer)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if layer in sel else Qt.Unchecked)
            self.listw.addItem(it)
        v.addWidget(self.listw, 1)
        btns = QtWidgets.QHBoxLayout()
        b_all = QtWidgets.QPushButton("All")
        b_none = QtWidgets.QPushButton("None")
        b_all.clicked.connect(lambda: self._set_all(True))
        b_none.clicked.connect(lambda: self._set_all(False))
        btns.addWidget(b_all)
        btns.addWidget(b_none)
        btns.addStretch(1)
        v.addLayout(btns)
        bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def _set_all(self, on):
        for i in range(self.listw.count()):
            self.listw.item(i).setCheckState(Qt.Checked if on else Qt.Unchecked)

    def result_layers(self):
        return [
            self.listw.item(i).data(Qt.UserRole)
            for i in range(self.listw.count())
            if self.listw.item(i).checkState() == Qt.Checked
        ]

    def result_mode(self):
        return "and" if self.rb_and.isChecked() else "or"


# --------------------------------------------------------------------------- #
#  Panneau de scenes (a gauche, toujours ouvert)
# --------------------------------------------------------------------------- #
# Meme forme d'arborescence des deux cotes, seuls les LIBELLES changent :
#   Shots/<SEQ>/<SHOT>/Scenefiles/<dept>/<task>/*.hip
#   Assets/<categorie>/<asset>/Scenefiles/<dept>/<task>/*.hip
# Une scene rangee sous Assets peut tres bien cacher de VRAIS shots (verifie sur
# frederic_2603 : Assets/FX/snowSetup, 77 imports tous en mode 'shot'). Aucun asset
# imbrique (categorie/sous-categorie/asset) sur yuka_2604 ni frederic_2603 (verifie).
SCENE_PATH_RE = re.compile(
    r"/(Shots|Assets)/([^/]+)/([^/]+)/Scenefiles/([^/]+)/([^/]+)/[^/]+$"
)


def _norm_path(p):
    """Chemin comparable (casse + separateurs) : le champ melange / et \\."""
    return os.path.normcase(os.path.normpath(p)) if p else ""


def scene_version(name):
    """Version d'un nom de scene (..._v012.hip -> 12 ; -1 si aucune) : tri des
    versions, la plus recente d'abord."""
    m = re.search(r"_v(\d+)\.[^.]+$", name) or re.search(r"v(\d+)", name)
    return int(m.group(1)) if m else -1


def list_entity_dirs(base):
    """[(nom, chemin)] des sous-dossiers a montrer, tries. Prism range les scenes de
    SEQUENCE sous un "shot" special nomme _sequence (ex SQ0010/_sequence/Scenefiles/
    Lighting/...) -> il faut le MONTRER, sinon les scenes lighting de sequence sont
    inatteignables. On cache les autres _*/.* (thumbnails, archives, dossiers
    techniques) et les gabarits Prism '@asset_path@' & co (pas des entites)."""
    if not base or not os.path.isdir(base):
        return []
    try:
        names = os.listdir(base)
    except Exception:
        return []
    out = []
    for n in sorted(names):
        if n.startswith("@") and n.endswith("@"):
            continue
        if n.startswith(".") or (n.startswith("_") and n != "_sequence"):
            continue
        full = os.path.join(base, n)
        if os.path.isdir(full):
            out.append((n, full))
    return out


def list_task_scenes(entity_dir):
    """[(dept, task, [scenes, la plus recente d'abord])] sous <entite>/Scenefiles/,
    pour les SEULES taches qui ont une scene .hip* / .ma : Prism cree des dossiers de
    tache vides a la pelle (14 sur 17 pour yuka SQ0020/SH0125). Le .mb, binaire,
    n'est pas lisible sans Maya -> jamais propose."""
    out = []
    for dept, dept_dir in list_entity_dirs(os.path.join(entity_dir, "Scenefiles")):
        for task, task_dir in list_entity_dirs(dept_dir):
            try:
                names = [
                    n for n in os.listdir(task_dir) if n.lower().endswith(PICKER_EXT)
                ]
            except Exception:
                continue
            if names:
                names.sort(key=scene_version, reverse=True)
                out.append((dept, task, [os.path.join(task_dir, n) for n in names]))
    return out


def _version_label(name, latest):
    """Libelle d'une version dans la colonne Task : 'v012' si le fichier est de la
    meme famille que la derniere version (meme nom au numero pres), sinon le nom
    complet (un fichier au nom different dans le dossier de tache ne doit pas se
    faire passer pour une simple version)."""
    stem = re.compile(r"_v\d+(\.[^.]+)$")
    m = re.search(r"_(v\d+)\.[^.]+$", name)
    if m and stem.sub(r"\1", name) == stem.sub(r"\1", latest):
        return m.group(1)
    return name


class SceneBrowser(QtWidgets.QWidget):
    """Panneau de gauche TOUJOURS OUVERT, en 3 colonnes : Sequence/Shot | Department
    | Task (remplace l'ancien 'Choose scene...'). L'arbre des entites (Shots :
    sequence > shot ; Assets : categorie > asset), puis les departements du shot qui
    ont des scenes, puis leurs taches : UNE ligne par tache = sa derniere version
    (deplier pour les anciennes). Un clic sur une tache / version charge la scene.

    Le departement/tache choisi est RETENU : cliquer un autre shot charge directement
    la meme tache s'il l'a -> on passe les shots d'une sequence en revue en un clic
    chacun. Tout est relu sur le disque a la volee (mesure : 0,05 s pour les 29
    sequences / 180 shots de frederic_2603, 0,08 s pour les 73 scenes d'un shot)."""

    sceneChosen = Signal(str)  # scene cliquee -> la fenetre la charge

    KINDS = ("Shots", "Assets")
    HEADERS = {"Shots": "Sequence / Shot", "Assets": "Category / Asset"}
    ROLE_TASK = Qt.UserRole + 1  # nom de la tache d'une ligne de la colonne Task
    COLUMN_SIZES = (210, 150, 200)  # Sequence/Shot | Department | Task (px)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.roots = {}
        self.kind = "Shots"
        self._entity = ""  # entite dont les colonnes Department / Task sont remplies
        self._tasks = {}  # {dept: [(tache, [scenes, plus recente d'abord])]}
        self._dept = ""  # departement dont les taches sont listees
        self._sticky = ("", "")  # (dept, tache) du dernier choix, suivi de shot en shot
        self._current = ""  # scene chargee dans la fenetre
        self._filtering = False
        self._last_toggle = None  # (item, instant) : un double-clic = UN seul toggle

        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)

        head = QtWidgets.QHBoxLayout()
        self.kind_group = QtWidgets.QButtonGroup(self)
        self.kind_group.setExclusive(True)
        self.kind_buttons = {}
        for kind in self.KINDS:
            b = QtWidgets.QPushButton(kind)
            b.setCheckable(True)
            self.kind_group.addButton(b)
            self.kind_buttons[kind] = b
            head.addWidget(b)
        self.kind_group.buttonClicked.connect(self._on_kind_clicked)
        v.addLayout(head)

        frow = QtWidgets.QHBoxLayout()
        self.ed_filter = QtWidgets.QLineEdit()
        self.ed_filter.setPlaceholderText("Filter (e.g. SH0125)")
        self.ed_filter.setClearButtonEnabled(True)
        self.ed_filter.setToolTip(
            "Show only the sequences / shots whose name contains this text\n"
            "(e.g. SH0125, SQ0020 or SQ0020/SH01). Enter = open the only match."
        )
        self.ed_filter.textChanged.connect(self._apply_filter)
        self.ed_filter.returnPressed.connect(self._open_single_match)
        frow.addWidget(self.ed_filter, 1)
        self.b_refresh = QtWidgets.QToolButton()
        self.b_refresh.setText("⟳")
        self.b_refresh.setToolTip("Re-read the project folders (new shots / scenes).")
        self.b_refresh.clicked.connect(self.refresh)
        frow.addWidget(self.b_refresh)
        v.addLayout(frow)

        # colonne 1 : entites
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setUniformRowHeights(True)
        # un clic deplie une sequence (cf _toggle_group) : le double-clic natif la
        # replierait aussitot
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.currentItemChanged.connect(self._on_entity_current)
        self.tree.itemClicked.connect(self._on_entity_clicked)
        self.tree.itemActivated.connect(self._on_entity_activated)

        # colonne 2 : departements (ceux qui ont au moins une scene)
        self.depts = QtWidgets.QTreeWidget()
        self.depts.setHeaderLabels(["Department"])
        self.depts.setRootIsDecorated(False)
        self.depts.setUniformRowHeights(True)
        self.depts.currentItemChanged.connect(self._on_dept_current)

        # colonne 3 : taches du departement (derniere version) + versions en enfants
        self.scenes = QtWidgets.QTreeWidget()
        self.scenes.setColumnCount(2)
        self.scenes.setHeaderLabels(["Task", "Version"])
        self.scenes.setUniformRowHeights(True)
        hdr = self.scenes.header()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.scenes.itemClicked.connect(self._on_scene_clicked)
        self.scenes.itemActivated.connect(self._on_scene_clicked)

        cols = QtWidgets.QSplitter(Qt.Horizontal)
        for i, w in enumerate((self.tree, self.depts, self.scenes)):
            cols.addWidget(w)
            cols.setStretchFactor(i, (4, 3, 4)[i])
        cols.setChildrenCollapsible(False)
        cols.setSizes(list(self.COLUMN_SIZES))
        v.addWidget(cols, 1)

        self.lbl_warn = QtWidgets.QLabel("")
        self.lbl_warn.setWordWrap(True)
        self.lbl_warn.setStyleSheet("color: %s;" % theme_colors(self)["orange"])
        self.lbl_warn.hide()
        v.addWidget(self.lbl_warn)
        self._set_kind("Shots", force=True)

    # ------------------------------------------------ projet / Shots-Assets
    def set_roots(self, roots):
        """Racines {'Shots': chemin, 'Assets': chemin} du projet courant. Appele a
        chaque changement de scene : ne relit le disque que si elles ont change."""
        roots = {k: v for k, v in (roots or {}).items() if v and os.path.isdir(v)}
        if roots == self.roots:
            return
        self.roots = roots
        for kind, b in self.kind_buttons.items():
            b.setEnabled(kind in roots)
            b.setToolTip(roots.get(kind) or "No %s folder in this project." % kind)
        kind = self.kind
        if kind not in roots:
            kind = next((k for k in self.KINDS if k in roots), kind)
        self._set_kind(kind, force=True)
        self._reveal(self._current)

    def _on_kind_clicked(self, button):
        self._set_kind(button.text())
        self._reveal(self._current, switch_kind=False)

    def _set_kind(self, kind, force=False):
        """Bascule Shots <-> Assets : meme arbre, autre racine, autres libelles."""
        if kind == self.kind and not force:
            return
        self.kind = kind
        self.kind_buttons[kind].setChecked(True)
        self.tree.setHeaderLabels([self.HEADERS[kind]])
        self._fill_tree()
        self._show_scenes("")
        self._apply_filter()
        self._warn_if_empty()

    def _fill_tree(self):
        self.tree.blockSignals(True)
        try:
            self.tree.clear()
            for top, top_dir in list_entity_dirs(self.roots.get(self.kind, "")):
                it = QtWidgets.QTreeWidgetItem(self.tree, [top])
                it.setFlags(Qt.ItemIsEnabled)  # un groupe (sequence), pas une entite
                for name, full in list_entity_dirs(top_dir):
                    ch = QtWidgets.QTreeWidgetItem(it, [name])
                    ch.setData(0, Qt.UserRole, full)
                    ch.setToolTip(0, full)
        finally:
            self.tree.blockSignals(False)

    def _warn_if_empty(self):
        if not self.roots:
            msg = (
                "No project selected/detected: pick one in 'Project' above, "
                "or 'Browse...' a scene."
            )
        elif not self.tree.topLevelItemCount():
            msg = "⚠ Nothing in %s" % self.roots.get(self.kind, "")
        else:
            msg = ""
        self.lbl_warn.setText(msg)
        self.lbl_warn.setVisible(bool(msg))

    def refresh(self):
        """Bouton ⟳ : relit le disque (nouveaux shots / scenes), selection gardee."""
        shown = self._entity
        self._fill_tree()
        self._apply_filter()
        self._warn_if_empty()
        self._entity = ""  # force la relecture des scenes
        if not self._reveal(self._current, switch_kind=False):
            item = self._find_entity_item(shown)
            if item is not None:
                self._select_entity_item(item)
                self._show_scenes(shown)

    # ------------------------------------------------------------- filtre
    def _apply_filter(self, *_):
        """Filtre sur 'sequence/shot' (insensible a la casse) : 'SH0125', 'SQ0020'
        ou 'SQ0020/SH01'. Une sequence qui correspond montre tous ses shots."""
        txt = self.ed_filter.text().strip().lower().replace("\\", "/")
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            shown = 0
            for j in range(top.childCount()):
                ch = top.child(j)
                hit = not txt or txt in ("%s/%s" % (top.text(0), ch.text(0))).lower()
                ch.setHidden(not hit)
                shown += hit
            top.setHidden(bool(txt) and not shown)
            if txt:
                top.setExpanded(bool(shown))
        if not txt and self._filtering:  # filtre efface : on replie sauf la selection
            self.tree.collapseAll()
            cur = self.tree.currentItem()
            if cur is not None and cur.parent() is not None:
                cur.parent().setExpanded(True)
                self.tree.scrollToItem(cur)
        self._filtering = bool(txt)

    def _open_single_match(self):
        """Entree dans le filtre : s'il ne reste qu'UN shot visible, on l'ouvre."""
        hits = []
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            if top.isHidden():
                continue
            for j in range(top.childCount()):
                if not top.child(j).isHidden():
                    hits.append(top.child(j))
        if len(hits) == 1:
            self._select_entity_item(hits[0])
            self._open_entity(hits[0])

    # ------------------------------------------------ colonne 1 : entites
    def _find_entity_item(self, entity):
        want = _norm_path(entity)
        if not want:
            return None
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            for j in range(top.childCount()):
                if _norm_path(top.child(j).data(0, Qt.UserRole)) == want:
                    return top.child(j)
        return None

    def _select_entity_item(self, item):
        self.tree.blockSignals(True)  # l'appelant remplit lui-meme les colonnes
        try:
            if item.parent() is not None:
                item.parent().setExpanded(True)
            self.tree.setCurrentItem(item)
        finally:
            self.tree.blockSignals(False)
        self.tree.scrollToItem(item)

    def _on_entity_current(self, cur, _prev=None):
        """Souris OU clavier : remplit Department / Task (rien n'est charge)."""
        entity = cur.data(0, Qt.UserRole) if cur is not None else ""
        if entity:
            self._show_scenes(entity)

    def _on_entity_clicked(self, item, _col=0):
        """Clic sur un shot : on l'ouvre. Clic sur une sequence : deplie / replie."""
        if item is None:
            return
        if item.data(0, Qt.UserRole):
            self._open_entity(item)
        else:
            self._toggle_group(item)

    def _on_entity_activated(self, item, _col=0):
        """Double-clic / Entree sur un shot = un clic. Rien sur une sequence : le clic
        l'a deja depliee (et les fleches du clavier deplient aussi)."""
        if item is not None and item.data(0, Qt.UserRole):
            self._open_entity(item)

    def _toggle_group(self, item):
        """Un double-clic envoie DEUX clics sur certaines versions de Qt : le second,
        dans l'intervalle de double-clic, est ignore -> toujours un seul toggle."""
        now = time.monotonic()
        last = self._last_toggle
        delay = QtWidgets.QApplication.doubleClickInterval() / 1000.0
        if last and last[0] is item and now - last[1] < delay:
            return
        self._last_toggle = (item, now)
        item.setExpanded(not item.isExpanded())

    def _open_entity(self, item):
        """Les colonnes du shot, et la MEME tache que le choix precedent si ce shot
        l'a : on passe les shots d'une sequence en revue en un clic chacun."""
        self._show_scenes(item.data(0, Qt.UserRole))
        dept, task = self._sticky
        row = self._task_row(task) if dept and self._dept == dept else None
        if row is not None:
            self._choose(row.data(0, Qt.UserRole))

    # ------------------------------------- colonnes 2 et 3 : dept / taches
    def _show_scenes(self, entity_dir, force=False):
        """Relit les scenes de l'entite et remplit la colonne Department. Departement
        affiche : celui de la scene chargee, sinon le dernier choisi, sinon le seul."""
        if entity_dir == self._entity and not force:
            return
        self._entity = entity_dir
        self._tasks = {}
        self._dept = ""
        self.depts.blockSignals(True)
        try:
            self.depts.clear()
            self.scenes.clear()
            if not entity_dir:
                return
            QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                listed = list_task_scenes(entity_dir)
            finally:
                QtWidgets.QApplication.restoreOverrideCursor()
            for dept, task, files in listed:
                self._tasks.setdefault(dept, []).append((task, files))
            if not self._tasks:
                it = QtWidgets.QTreeWidgetItem(self.depts, ["no .hip / .ma scene"])
                it.setFlags(Qt.NoItemFlags)
                return
            for dept, tasks in self._tasks.items():
                it = QtWidgets.QTreeWidgetItem(self.depts, [dept])
                it.setData(0, Qt.UserRole, dept)
                it.setToolTip(0, ", ".join(t for t, _ in tasks))
        finally:
            self.depts.blockSignals(False)
        dept = self._dept_of_current()
        if not dept and self._sticky[0] in self._tasks:
            dept = self._sticky[0]
        if not dept and len(self._tasks) == 1:
            dept = next(iter(self._tasks))
        if dept:
            self._select_dept(dept)

    def _dept_of_current(self):
        """Departement de la scene chargee si elle appartient a l'entite affichee."""
        m = SCENE_PATH_RE.search((self._current or "").replace("\\", "/"))
        if not m or not self._entity:
            return ""
        entity = self._current
        for _ in range(4):  # <entite>/Scenefiles/<dept>/<tache>/<scene>
            entity = os.path.dirname(entity)
        return m.group(4) if _norm_path(entity) == _norm_path(self._entity) else ""

    def _select_dept(self, dept):
        for i in range(self.depts.topLevelItemCount()):
            it = self.depts.topLevelItem(i)
            if it.data(0, Qt.UserRole) == dept:
                self.depts.blockSignals(True)
                try:
                    self.depts.setCurrentItem(it)
                finally:
                    self.depts.blockSignals(False)
                break
        self._show_tasks(dept)

    def _on_dept_current(self, cur, _prev=None):
        """Souris OU clavier sur un departement : ses taches (rien n'est charge)."""
        dept = cur.data(0, Qt.UserRole) if cur is not None else ""
        if dept:
            self._show_tasks(dept)

    def _show_tasks(self, dept):
        """Colonne Task : une ligne par tache = sa derniere version, les versions en
        enfants (plus recente d'abord)."""
        self._dept = dept
        self.scenes.clear()
        for task, files in self._tasks.get(dept, []):
            latest = os.path.basename(files[0])
            row = QtWidgets.QTreeWidgetItem(
                self.scenes, [task, _version_label(latest, latest)]
            )
            row.setData(0, Qt.UserRole, files[0])
            row.setData(0, self.ROLE_TASK, task)
            tip = (
                "%s\nClick = load this latest version. Unfold for older ones." % latest
            )
            row.setToolTip(0, tip)
            row.setToolTip(1, tip)
            for f in files:
                ch = QtWidgets.QTreeWidgetItem(
                    row, [_version_label(os.path.basename(f), latest)]
                )
                ch.setData(0, Qt.UserRole, f)
                ch.setToolTip(0, f)
        self._mark_current()

    def _task_row(self, task):
        if not task:
            return None
        for i in range(self.scenes.topLevelItemCount()):
            row = self.scenes.topLevelItem(i)
            if row.data(0, self.ROLE_TASK) == task:
                return row
        return None

    def _mark_current(self):
        """Selectionne la scene chargee dans la fenetre : la ligne de sa tache si c'est
        la derniere version, sinon la version exacte (tache depliee). True si trouvee."""
        want = _norm_path(self._current)
        self.scenes.clearSelection()
        if not want:
            return False
        for i in range(self.scenes.topLevelItemCount()):
            row = self.scenes.topLevelItem(i)
            for j in range(row.childCount()):
                if _norm_path(row.child(j).data(0, Qt.UserRole)) != want:
                    continue
                target = row if j == 0 else row.child(j)
                if j:
                    row.setExpanded(True)
                self.scenes.setCurrentItem(target)
                self.scenes.scrollToItem(target)
                return True
        return False

    def _on_scene_clicked(self, item, _col=0):
        """Clic sur une tache = sa derniere version ; sur une version = celle-la."""
        path = item.data(0, Qt.UserRole) if item is not None else ""
        if not path:
            return
        row = item.parent() or item
        self._sticky = (self._dept, row.data(0, self.ROLE_TASK) or "")
        self._choose(path)

    def _choose(self, path):
        """La scene part dans la fenetre, une seule fois (un double-clic = 2 clics)."""
        if _norm_path(path) != _norm_path(self._current):
            self._current = path
            self.sceneChosen.emit(path)
        self._mark_current()

    # ------------------------------------------ la fenetre a change de scene
    def select_path(self, path):
        """La fenetre a charge `path` (champ Scene, Browse, From scene, version-up) :
        le panneau le montre, SANS rien recharger."""
        if _norm_path(path) == _norm_path(self._current):
            return
        self._current = path or ""
        if not self._reveal(self._current):
            self._mark_current()  # scene hors projet : plus rien de selectionne

    def _reveal(self, path, switch_kind=True):
        """Selectionne l'entite, le departement et la tache de `path` s'il est range
        dans le projet courant. False sinon (scene hors projet, ou de l'autre cote
        Shots/Assets quand `switch_kind` est faux)."""
        m = SCENE_PATH_RE.search((path or "").replace("\\", "/"))
        if not m or m.group(1) not in self.roots:
            return False
        kind, dept, task = m.group(1), m.group(4), m.group(5)
        entity = os.path.join(self.roots[kind], m.group(2), m.group(3))
        if not _norm_path(path).startswith(_norm_path(entity) + os.sep):
            return False  # memes noms de dossiers, mais un autre projet
        if kind != self.kind:
            if not switch_kind:
                return False
            self._set_kind(kind)
        item = self._find_entity_item(entity)
        if item is not None:
            self._select_entity_item(item)
        self._sticky = (dept, task)
        for force in (False, True):  # 2e passe : scene toute neuve (version-up), relire
            self._show_scenes(entity, force=force)
            if self._dept != dept:
                self._select_dept(dept)
            if self._mark_current():
                break
        return True


# --------------------------------------------------------------------------- #
#  Presets de scene (partages par projet)
# --------------------------------------------------------------------------- #
# Un preset = un NOM ("cfx brush") -> une scene du projet, que tout le monde charge en
# un clic sans savoir ou elle est rangee. On stocke la FAMILLE de la scene (dossier de
# tache + nom sans version), pas un fichier : le preset suit les version-ups et ouvre
# toujours la DERNIERE version. Un json par projet, avec les autres configs projet de
# Prism (launcher.json, omits.json) :
#   <projet>/00_Pipeline/Configs/lop_update_cache_presets.json
# Surtout PAS 00_Pipeline/PresetScenes : c'est le dossier des gabarits de scene de
# Prism, il les proposerait a la creation d'une scene.
PRESETS_FILE = "lop_update_cache_presets.json"


def scene_family(path):
    """Nom de scene sans version ni extension (SQ0020-SH0090_FX_v024.hip ->
    SQ0020-SH0090_FX) : cle des sidecars ET des presets, stable aux version-ups."""
    base = os.path.splitext(os.path.basename(path or ""))[0]
    return re.sub(r"_v\d+", "", base) or base


def presets_path(project_cfg):
    """<projet>/00_Pipeline/Configs/<PRESETS_FILE> depuis le pipeline.json."""
    if not project_cfg:
        return ""
    return os.path.join(os.path.dirname(project_cfg), "Configs", PRESETS_FILE)


def read_presets(project_cfg):
    """Presets du projet [{name, path, scene, created_by, created_at}], dans l'ordre
    d'enregistrement. [] si aucun fichier ou fichier illisible."""
    p = presets_path(project_cfg)
    if not p or not os.path.isfile(p):
        return []
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    entries = data.get("presets") if isinstance(data, dict) else None
    return [
        e
        for e in entries or []
        if isinstance(e, dict) and e.get("name") and e.get("path") and e.get("scene")
    ]


def write_presets(project_cfg, presets):
    """Ecrit la liste via un fichier temporaire + remplacement : jamais de json a
    moitie ecrit, meme si deux personnes enregistrent en meme temps."""
    p = presets_path(project_cfg)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = "%s.%d.tmp" % (p, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "presets": presets}, f, indent=2)
    os.replace(tmp, p)


def make_preset(project_cfg, name, scene, user):
    """Preset pointant la famille de `scene`, qui doit etre DANS le projet
    (ValueError sinon : un chemin relatif hors projet ne voudrait rien dire)."""
    root = os.path.dirname(os.path.dirname(project_cfg))
    try:
        rel = os.path.relpath(os.path.dirname(os.path.abspath(scene)), root)
    except ValueError:  # autre lecteur
        rel = ".."
    if rel == "." or rel.startswith(".."):
        raise ValueError("the scene is not inside the project %s" % root)
    return {
        "name": name,
        "path": rel.replace("\\", "/"),
        "scene": scene_family(scene),
        "created_by": user,
        "created_at": time.strftime("%Y-%m-%d %H:%M"),
    }


def preset_task_dir(project_cfg, preset):
    root = os.path.dirname(os.path.dirname(project_cfg))
    return os.path.join(root, *preset["path"].split("/"))


def preset_scene(project_cfg, preset):
    """DERNIERE version de la scene du preset ('' si elle n'existe plus : renommee,
    deplacee, supprimee)."""
    task_dir = preset_task_dir(project_cfg, preset)
    try:
        names = [
            n
            for n in os.listdir(task_dir)
            if n.lower().endswith(PICKER_EXT) and scene_family(n) == preset["scene"]
        ]
    except OSError:
        return ""
    return os.path.join(task_dir, max(names, key=scene_version)) if names else ""


def preset_where(preset):
    """'Shots/MASTER/MT0010 · CFX/CFX' : ou vit la scene, pour l'infobulle."""
    path = preset["path"]
    if path.startswith("03_Production/"):
        path = path[len("03_Production/") :]
    return path.replace("/Scenefiles/", " · ")


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


class CachePickerDialog(QtWidgets.QDialog):
    """Choix des lop_filecache a executer pour un shot. Un shot peut en avoir PLUSIEURS,
    publiant des produits differents (verifie : `_layer_fx_snow_still` ET
    `_layer_fx_snow_sim` sur le meme shot). On les identifie par leur PRODUIT, pas par
    leur nom de node : 'lop_filecache3' ne dit rien, '_layer_fx_snow_sim' si.
    Tout decocher = pas de re-cache (l'import est quand meme bumpe, le render soumis).
    'Apply to all shots' propage PAR PRODUIT (les noms de node different d'un shot a
    l'autre, les produits non). Retourne les CHEMINS coches."""

    def __init__(self, parent, shot, caches, checked_paths):
        super().__init__(parent)
        self.setWindowTitle("Caches to re-cache - %s" % shot)
        self.resize(620, 380)
        v = QtWidgets.QVBoxLayout(self)
        v.addWidget(
            QtWidgets.QLabel(
                "Tick the USD caches to re-cache for this shot. Default = all of them. "
                "Unticking all = no re-cache (the import is still bumped, and the "
                "render still submitted)."
            )
        )
        self.listw = QtWidgets.QListWidget()
        for c in caches:  # [{path, name, product}]
            prod = c.get("product") or "(product unknown)"
            it = QtWidgets.QListWidgetItem("%s     [%s]" % (prod, c.get("name") or ""))
            it.setToolTip(c.get("path") or "")
            it.setData(Qt.UserRole, c.get("path"))
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(
                Qt.Checked
                if c.get("path") in (checked_paths or set())
                else Qt.Unchecked
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
            "On OK, copy this selection (by PRODUCT) to every other shot."
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

    def checked_paths(self):
        return [
            self.listw.item(i).data(Qt.UserRole)
            for i in range(self.listw.count())
            if self.listw.item(i).checkState() == Qt.Checked
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


class ExportPickerDialog(QtWidgets.QDialog):
    """Choix des exports Prism a lancer APRES la mise a jour des rigs d'une scene Maya.
    Un export = un state du State Manager de la scene, identifie par son produit
    (`_layer_anm_main`) plutot que par son nom de state. Defaut = les states coches dans
    le State Manager de la scene (comme les renders : defaut = Enabled sur le node).
    Tout decocher = pas d'export (mise a jour + sauvegarde seules). Retourne les uuids."""

    def __init__(self, parent, scene_name, exports, checked_uuids):
        super().__init__(parent)
        self.setWindowTitle("Exports after the update - %s" % scene_name)
        self.resize(620, 360)
        v = QtWidgets.QVBoxLayout(self)
        v.addWidget(
            QtWidgets.QLabel(
                "Tick the Prism exports to run once the rigs are updated (and the scene "
                "saved).\nDefault = the states ticked in the scene's State Manager. "
                "Unticking all = no export."
            )
        )
        self.listw = QtWidgets.QListWidget()
        for e in exports:  # [{uuid, name, product, enabled, output_type, latest}]
            tags = []
            if e.get("latest"):
                tags.append("last %s" % e["latest"])
            if not e.get("enabled"):
                tags.append("unticked in the scene")
            it = QtWidgets.QListWidgetItem(
                "%s   →  %s %s%s"
                % (
                    e.get("name") or "?",
                    e.get("product") or "(product unknown)",
                    e.get("output_type") or "",
                    ("   (%s)" % ", ".join(tags)) if tags else "",
                )
            )
            it.setToolTip("%s state  ·  uuid %s" % (e.get("stateclass"), e.get("uuid")))
            it.setData(Qt.UserRole, e.get("uuid"))
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(
                Qt.Checked
                if e.get("uuid") in (checked_uuids or set())
                else Qt.Unchecked
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

    def checked_uuids(self):
        return [
            self.listw.item(i).data(Qt.UserRole)
            for i in range(self.listw.count())
            if self.listw.item(i).checkState() == Qt.Checked
        ]


# --------------------------------------------------------------------------- #
#  Reglages ferme (Deadline) des renders
# --------------------------------------------------------------------------- #
# Les MEMES champs que la fenetre de submit Prism d'un LOP_Render ; l'outil les pose sur
# le state avant le submit (recache_cfx.apply_farm_settings, --farm-plan). Un champ non
# coche garde la valeur de la scene (chaque render a les siennes).
FRAME_PRESETS = (
    "{first}, {middle}, {last}",
    "{first}-{last}x10",
    "{first}-{last}x5",
    "{first}",
    "{last}",
)
_FRAME_EXPR_RE = re.compile(r"^[\d\s,x:-]+$")


def check_frame_expression(expr):
    """Message d'erreur si l'expression de frames est inutilisable, sinon ''. Tokens
    {first} {middle} {last} = la plage de CHAQUE shot (resolus par le moteur)."""
    if not (expr or "").strip():
        return "empty frame expression"
    try:
        concrete = expr.format(first=1001, middle=1050, last=1100)
    except (KeyError, IndexError, ValueError) as e:
        return "unknown token in '%s' (%s) - use {first} {middle} {last}" % (expr, e)
    if not _FRAME_EXPR_RE.match(concrete):
        return "invalid frame expression '%s' (e.g. 1001-1100x10, 1001,1050)" % expr
    return ""


def farm_values(data):
    """Reglages ferme des renders de la scene (status JSON) -> [dict par render]."""
    out = []
    for d in data or []:
        for r in d.get("renders") or []:
            if isinstance(r.get("farm"), dict):
                out.append(r["farm"])
    return out


def has_renders(data):
    return any(d.get("renders") for d in data or [])


def pins_text(pins):
    """{'anm': 'v018'} -> 'anm v018' (lignes epinglees d'un usd_layer_stack)."""
    return ", ".join("%s %s" % (d, v) for d, v in sorted((pins or {}).items()))


def scene_value_text(farms, key, sub=None):
    """'65' si tous les renders ont la meme valeur, '60-65' / 'a, b' sinon."""
    vals = []
    for f in farms:
        v = f.get(key)
        if sub is not None and isinstance(v, dict):
            v = v.get(sub)
        if v is not None and v not in vals:
            vals.append(v)
    if not vals:
        return "?"
    if len(vals) == 1:
        v = vals[0]
        return ("on" if v else "off") if isinstance(v, bool) else str(v)
    if all(isinstance(v, int) and not isinstance(v, bool) for v in vals):
        return "%s-%s (per render)" % (min(vals), max(vals))
    if all(isinstance(v, bool) for v in vals):
        return "on for some renders, off for others"
    return ", ".join(str(v) for v in vals[:4]) + (" ..." if len(vals) > 4 else "")


def scene_frames_text(farms):
    ranges = sorted(
        {
            (f["first"], f["last"])
            for f in farms
            if f.get("first") is not None and f.get("last") is not None
        }
    )
    if not ranges:
        return "?"
    if len(ranges) == 1:
        return "%s-%s" % ranges[0]
    return "%s-%s ... %s-%s (each shot its own range)" % (ranges[0] + ranges[-1])


def farm_overrides_text(ov):
    """Resume lisible des overrides (bouton, confirmation). '' = reglages de la scene."""
    if not ov:
        return ""
    parts = []
    fr = ov.get("frames") or {}
    if fr.get("mode") == "range":
        parts.append("frames %s-%s" % (fr.get("start"), fr.get("end")))
    elif fr.get("mode") == "expression":
        parts.append("frames %s" % fr.get("expr"))
    for key, label in (
        ("priority", "priority %s"),
        ("chunk", "%s frame(s)/task"),
        ("machine_limit", "machine limit %s"),
        ("timeout", "timeout %s min"),
        ("concurrent", "%s concurrent task(s)"),
        ("pool", "pool %s"),
        ("secondary_pool", "secondary pool %s"),
        ("group", "group %s"),
    ):
        if ov.get(key) not in (None, ""):
            parts.append(label % ov[key])
    if ov.get("suspended") is not None:
        parts.append("submitted SUSPENDED" if ov["suspended"] else "not suspended")
    hp = ov.get("high_prio") or {}
    if hp:
        if hp.get("enabled") is False:
            parts.append("no high-prio job")
        else:
            parts.append(
                "high-prio job %s on %s" % (hp.get("priority"), hp.get("frames"))
            )
    return ", ".join(parts)


class FarmSettingsDialog(QtWidgets.QDialog):
    """Reglages ferme des renders soumis par cet update : frames, priorite, chunk, pool,
    group, machine limit, suspended, job haute prio. Chaque ligne a une case 'override' :
    decochee = la valeur de la scene (affichee a droite), pour chaque render."""

    def __init__(self, parent, farms, overrides):
        super().__init__(parent)
        self.setWindowTitle("Farm settings - renders of this update")
        self.resize(760, 560)
        self.farms = farms or []
        ov = overrides or {}
        first = self.farms[0] if self.farms else {}
        v = QtWidgets.QVBoxLayout(self)
        intro = QtWidgets.QLabel(
            "Same settings as the Prism submit window of a LOP Render. Tick a setting to "
            "override it for EVERY render of this update; unticked = each render keeps "
            "its own value from the scene (shown on the right)."
        )
        intro.setWordWrap(True)
        v.addWidget(intro)
        if not self.farms:
            warn = QtWidgets.QLabel(
                "⚠ The scene's current values are unknown (cached state from an older "
                "version of the tool): run 'Load Scene (slow)' to read them."
            )
            warn.setWordWrap(True)
            warn.setStyleSheet("color: %s;" % theme_colors(self)["orange"])
            v.addWidget(warn)
        grid = QtWidgets.QGridLayout()
        grid.setColumnStretch(1, 1)
        v.addLayout(grid)
        self.rows = {}  # cle -> (case override, [editeurs])
        gray = theme_colors(self)["gray"]

        def add(key, label, editors, scene_txt, tip=""):
            r = grid.rowCount()
            chk = QtWidgets.QCheckBox(label)
            chk.setToolTip(tip)
            box = QtWidgets.QHBoxLayout()
            for e in editors:
                box.addWidget(e)
            box.addStretch(1)
            hint = QtWidgets.QLabel("scene: %s" % scene_txt)
            hint.setStyleSheet("color: %s;" % gray)
            hint.setToolTip(tip)
            grid.addWidget(chk, r, 0)
            grid.addLayout(box, r, 1)
            grid.addWidget(hint, r, 2)
            chk.toggled.connect(lambda on, es=editors: [e.setEnabled(on) for e in es])
            self.rows[key] = (chk, editors)
            return chk

        def spin(lo, hi, value):
            s = QtWidgets.QSpinBox()
            s.setRange(lo, hi)
            s.setValue(int(value if value is not None else lo))
            return s

        # --- frames ---
        fr = ov.get("frames") or {}
        self.cb_frames = QtWidgets.QComboBox()
        self.cb_frames.addItems(["Range", "Expression"])
        self.sp_start = spin(0, 99999, fr.get("start", first.get("first") or 1001))
        self.sp_end = spin(0, 99999, fr.get("end", first.get("last") or 1100))
        self.ed_expr = QtWidgets.QLineEdit(fr.get("expr") or FRAME_PRESETS[0])
        self.ed_expr.setMinimumWidth(200)
        self.ed_expr.setToolTip(
            "{first} {middle} {last} = the frame range of EACH shot.\n"
            "e.g. {first}-{last}x10 = every 10th frame, {first}, {middle}, {last} = 3 "
            "frames per shot. Plain frames work too: 1001-1050, 1001,1020."
        )
        self.b_expr = QtWidgets.QToolButton()
        self.b_expr.setText("▾")
        self.b_expr.setToolTip("Presets")
        menu = QtWidgets.QMenu(self.b_expr)
        for p in FRAME_PRESETS:
            menu.addAction(p).triggered.connect(
                lambda _=False, p=p: self.ed_expr.setText(p)
            )
        self.b_expr.setMenu(menu)
        self.b_expr.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.lbl_to = QtWidgets.QLabel("to")
        if fr.get("mode") == "expression":
            self.cb_frames.setCurrentIndex(1)
        self.cb_frames.currentIndexChanged.connect(self._sync_frames)
        add(
            "frames",
            "Frames",
            [
                self.cb_frames,
                self.sp_start,
                self.lbl_to,
                self.sp_end,
                self.ed_expr,
                self.b_expr,
            ],
            scene_frames_text(self.farms),
            "Range = the same frames for every shot. Expression = tokens resolved per "
            "shot.",
        )
        # --- reglages du job ---
        self.sp_prio = spin(0, 100, ov.get("priority", first.get("priority") or 50))
        add(
            "priority",
            "Priority",
            [self.sp_prio],
            scene_value_text(self.farms, "priority"),
        )
        self.sp_chunk = spin(1, 9999, ov.get("chunk", first.get("chunk") or 1))
        add(
            "chunk",
            "Frames per task",
            [self.sp_chunk],
            scene_value_text(self.farms, "chunk"),
            "Tile renders need 1 frame per task (studio sanity check TileFramePerTask).",
        )
        self.sp_machines = spin(
            0, 99999, ov.get("machine_limit", first.get("machine_limit") or 0)
        )
        add(
            "machine_limit",
            "Machine limit",
            [self.sp_machines],
            scene_value_text(self.farms, "machine_limit"),
            "0 = no limit.",
        )
        self.sp_timeout = spin(1, 9999, ov.get("timeout", first.get("timeout") or 180))
        add(
            "timeout",
            "Task timeout (min)",
            [self.sp_timeout],
            scene_value_text(self.farms, "timeout"),
        )
        self.sp_concurrent = spin(
            1, 99, ov.get("concurrent", first.get("concurrent") or 1)
        )
        add(
            "concurrent",
            "Concurrent tasks",
            [self.sp_concurrent],
            scene_value_text(self.farms, "concurrent"),
        )

        def choices(key, single):
            items = []
            for f in self.farms:
                for x in f.get(key) or []:
                    if x not in items:
                        items.append(x)
            cur = ov.get(single) or first.get(single)
            if cur and cur not in items:
                items.append(cur)
            cb = QtWidgets.QComboBox()
            cb.addItems(items)
            if cur:
                cb.setCurrentText(cur)
            return cb

        self.cb_pool = choices("pools", "pool")
        add("pool", "Pool", [self.cb_pool], scene_value_text(self.farms, "pool"))
        self.cb_pool2 = choices("pools", "secondary_pool")
        add(
            "secondary_pool",
            "Secondary pool",
            [self.cb_pool2],
            scene_value_text(self.farms, "secondary_pool"),
        )
        self.cb_group = choices("groups", "group")
        husk = next(
            (f.get("husk_group_env") for f in self.farms if f.get("husk_group_env")), ""
        )
        add(
            "group",
            "Group",
            [self.cb_group],
            scene_value_text(self.farms, "group")
            + (" (husk render job: %s, set by the project)" % husk if husk else ""),
            (
                "The project forces the group of the husk RENDER job (%s, "
                "PRISM_HUSK_DEADLINE_GROUP): this group applies to the other jobs."
                % husk
            )
            if husk
            else "",
        )
        self.cb_susp = QtWidgets.QComboBox()
        self.cb_susp.addItems(["No", "Yes"])
        self.cb_susp.setCurrentIndex(
            1 if ov.get("suspended", first.get("suspended")) else 0
        )
        add(
            "suspended",
            "Submit suspended",
            [self.cb_susp],
            scene_value_text(self.farms, "suspended"),
            "Yes = the jobs wait in Deadline until someone resumes them.",
        )
        hp = ov.get("high_prio") or {}
        fhp = first.get("high_prio") or {}
        self.cb_hp = QtWidgets.QComboBox()
        self.cb_hp.addItems(["Off", "On"])
        self.cb_hp.setCurrentIndex(1 if hp.get("enabled", fhp.get("enabled")) else 0)
        self.sp_hp = spin(0, 100, hp.get("priority", fhp.get("priority") or 70))
        self.ed_hp = QtWidgets.QLineEdit(
            hp.get("frames") or fhp.get("frames") or FRAME_PRESETS[0]
        )
        self.ed_hp.setMinimumWidth(170)
        self.ed_hp.setToolTip(
            "Frames rendered first in a separate high-priority job ({first} {middle} "
            "{last} of the job's frames)."
        )
        hp_txt = scene_value_text(self.farms, "high_prio", "enabled")
        if hp_txt == "on":
            hp_txt = "on, priority %s on %s" % (
                scene_value_text(self.farms, "high_prio", "priority"),
                scene_value_text(self.farms, "high_prio", "frames"),
            )
        add(
            "high_prio",
            "High-prio job",
            [self.cb_hp, QtWidgets.QLabel("priority"), self.sp_hp, self.ed_hp],
            hp_txt,
            "Prism's 'Submit High Prio Job': the chosen frames go first, at their own "
            "priority; the rest follows in the normal job.",
        )
        # etat initial des cases : coche = override deja demande
        for key, (chk, editors) in self.rows.items():
            on = key in ov
            chk.setChecked(on)
            for e in editors:
                e.setEnabled(on)
        self._sync_frames()

        self.lbl_error = QtWidgets.QLabel("")
        self.lbl_error.setStyleSheet("color: %s;" % theme_colors(self)["red"])
        v.addWidget(self.lbl_error)
        v.addStretch(1)
        row = QtWidgets.QHBoxLayout()
        b_reset = QtWidgets.QPushButton("Use the scene's settings")
        b_reset.setToolTip("Untick everything: each render keeps its own settings.")
        b_reset.clicked.connect(
            lambda: [c.setChecked(False) for c, _ in self.rows.values()]
        )
        row.addWidget(b_reset)
        row.addStretch(1)
        v.addLayout(row)
        bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        bb.accepted.connect(self._accept)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def _sync_frames(self, *_):
        expr = self.cb_frames.currentIndex() == 1
        for w in (self.sp_start, self.lbl_to, self.sp_end):
            w.setVisible(not expr)
        for w in (self.ed_expr, self.b_expr):
            w.setVisible(expr)

    def overrides(self):
        """Les reglages coches -> dict pour --farm-plan (cles absentes = scene)."""
        on = {k for k, (chk, _) in self.rows.items() if chk.isChecked()}
        ov = {}
        if "frames" in on:
            if self.cb_frames.currentIndex() == 1:
                ov["frames"] = {
                    "mode": "expression",
                    "expr": self.ed_expr.text().strip(),
                }
            else:
                ov["frames"] = {
                    "mode": "range",
                    "start": self.sp_start.value(),
                    "end": self.sp_end.value(),
                }
        for key, w in (
            ("priority", self.sp_prio),
            ("chunk", self.sp_chunk),
            ("machine_limit", self.sp_machines),
            ("timeout", self.sp_timeout),
            ("concurrent", self.sp_concurrent),
        ):
            if key in on:
                ov[key] = w.value()
        for key, w in (
            ("pool", self.cb_pool),
            ("secondary_pool", self.cb_pool2),
            ("group", self.cb_group),
        ):
            if key in on and w.currentText():
                ov[key] = w.currentText()
        if "suspended" in on:
            ov["suspended"] = self.cb_susp.currentIndex() == 1
        if "high_prio" in on:
            enabled = self.cb_hp.currentIndex() == 1
            ov["high_prio"] = (
                {
                    "enabled": True,
                    "priority": self.sp_hp.value(),
                    "frames": self.ed_hp.text().strip(),
                }
                if enabled
                else {"enabled": False}
            )
        return ov

    def validation_error(self):
        ov = self.overrides()
        fr = ov.get("frames") or {}
        if fr.get("mode") == "range" and fr["start"] > fr["end"]:
            return "Frames: the start (%s) is after the end (%s)." % (
                fr["start"],
                fr["end"],
            )
        if fr.get("mode") == "expression":
            err = check_frame_expression(fr["expr"])
            if err:
                return "Frames: %s." % err
        hp = ov.get("high_prio") or {}
        if hp.get("enabled"):
            err = check_frame_expression(hp.get("frames"))
            if err:
                return "High-prio job: %s." % err
        return ""

    def _accept(self):
        err = self.validation_error()
        if err:
            self.lbl_error.setText(err)
            return
        self.accept()


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
        # 1560x900 + 20 % (panneau de scenes en 3 colonnes), borne a l'ecran : plus
        # grande que l'ecran, la fenetre passerait sous la barre des taches
        w, h = 1872, 1080
        scr = self.screen() or QtGui.QGuiApplication.primaryScreen()
        if scr is not None:
            avail = scr.availableGeometry()
            w = min(w, int(avail.width() * 0.95))
            h = min(h, int(avail.height() * 0.95))
        self.resize(w, h)
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
        self._cache_selection = {}  # shot -> [chemins de caches coches]
        self._fx_store = (
            None  # json partage a cote du hip (lazy) : snapshot + selections
        )
        self._scan = None  # _ScanWorker en cours (preview disque en tache de fond)
        self._previewed = None  # hip deja preview (evite les re-preview au keystroke)
        # --- scene Maya (mode RIGS) ---
        self._kind = None  # 'houdini' | 'maya' | '' : type de la scene du champ
        self._maya_rigs = []  # rig_status de la scene .ma (une ligne par asset)
        self._maya_exports = []  # states d'export Prism de la scene .ma
        self._maya_read = (
            None  # (chemin, mtime) deja lu -> pas de relecture au keystroke
        )
        self._export_selection = None  # uuids coches (None = defaut de la scene)
        # reglages ferme demandes pour les renders de CET update (overrides, {} = ceux
        # de la scene). En memoire seulement : la prio se decide au moment d'envoyer.
        self._farm_overrides = {}
        self._farm_for = None  # cle de la scene pour laquelle ils ont ete choisis
        self._run_scene = ""  # scene du run Maya en cours (le champ peut bouger)
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
        # QSettings ne restitue pas fidelement une liste -> on renormalise, avec repli
        # sur l'ancienne cle mono-layer pour ne rien perdre d'une config existante.
        self.cfg["tracked_layers"] = as_layer_list(
            self.cfg.get("tracked_layers")
        ) or as_layer_list(self.cfg.get("tracked_layer"))
        self.cfg["hython"] = detect_hython(self.cfg.get("hython"))
        self.cfg["mayapy"] = detect_mayapy(self.cfg.get("mayapy"))
        self.cfg["project_override"] = self.settings.value("project_override", "")
        self.last_hip = self.settings.value("last_hip", "")
        # lance depuis Houdini : pre-remplir la scene courante si rien de memorise
        if not self.last_hip:
            envhip = os.environ.get(ENV_HIP, "")
            if envhip and os.path.isfile(envhip):
                self.last_hip = envhip

    def _save_settings(self):
        for k in list(DEFAULT_SETTINGS.keys()) + ["project_override"]:
            v = self.cfg.get(k, "")
            if k == "tracked_layers":  # liste -> chaine (QSettings, cf as_layer_list)
                v = ",".join(as_layer_list(v))
            self.settings.setValue(k, v)
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

        # --- zone de travail, a droite du panneau de scenes (monte plus bas) ---
        work = QtWidgets.QWidget()
        wlay = QtWidgets.QVBoxLayout(work)
        wlay.setContentsMargins(0, 0, 0, 0)

        # --- scene row ---
        bar = QtWidgets.QHBoxLayout()
        bar.addWidget(QtWidgets.QLabel("Scene:"))
        self.ed_hip = QtWidgets.QLineEdit(self.last_hip)
        self.ed_hip.setToolTip(
            "The scene to update: a Houdini .hip (caches / renders) or a Maya .ma "
            "(rigs + exports)."
        )
        self.ed_hip.textChanged.connect(self._on_hip_changed)
        bar.addWidget(self.ed_hip, 1)
        # presets PARTAGES par projet ("cfx brush" -> derniere version de la scene, sans
        # savoir ou elle est) : menu relu a chaque ouverture (cf read_presets)
        self._presets_prj = None  # projet dont le compte de presets est affiche
        self.b_presets = QtWidgets.QPushButton("★ Presets")
        self.presets_menu = QtWidgets.QMenu(self.b_presets)
        self.presets_menu.setToolTipsVisible(True)
        self.presets_menu.aboutToShow.connect(self._fill_presets_menu)
        # sous-menu cree UNE fois et re-rattache a chaque ouverture : un addMenu(titre)
        # par ouverture empile des QMenu (clear() ne les detruit pas) et PySide finit
        # par renvoyer un wrapper deja detruit (vu en test)
        self.presets_delete_menu = QtWidgets.QMenu("Delete preset", self.presets_menu)
        self.b_presets.setMenu(self.presets_menu)
        bar.addWidget(self.b_presets)
        # la scene OUVERTE dans Houdini (passee par le shelf au lancement), en un clic :
        # le champ, lui, reprend la derniere scene memorisee
        self.b_from_scene = QtWidgets.QPushButton("From scene")
        self.b_from_scene.clicked.connect(self._use_houdini_scene)
        bar.addWidget(self.b_from_scene)
        self._refresh_from_scene_button()
        b_hip = QtWidgets.QPushButton("Browse...")
        b_hip.setToolTip("Pick a .hip or a .ma anywhere on the filesystem.")
        b_hip.clicked.connect(self._pick_hip)
        bar.addWidget(b_hip)
        b_set = QtWidgets.QPushButton("Settings...")
        b_set.setToolTip("hython path, node convention, reset (persisted).")
        b_set.clicked.connect(self._open_settings)
        bar.addWidget(b_set)
        wlay.addLayout(bar)

        # --- layer + actions row ---
        top = QtWidgets.QHBoxLayout()
        self.lbl_layer = QtWidgets.QLabel("Tracked layer:")
        top.addWidget(self.lbl_layer)
        # Cas courant = UN layer, dans un simple dropdown (lisible d'un coup d'oeil).
        # Le multi-layer + OU/ET vit derriere la roue crantee : puissant sans encombrer.
        self.combo_layer = QtWidgets.QComboBox()
        self.combo_layer.setMinimumWidth(240)
        self.combo_layer.setToolTip(
            "The USD layer whose version decides if a shot is outdated.\n"
            "Filled from the layers this scene really consumes.\n"
            "Use the gear to track SEVERAL layers at once (ANY / ALL)."
        )
        self.combo_layer.currentIndexChanged.connect(self._on_layer_changed)
        top.addWidget(self.combo_layer)
        self.b_layer_adv = QtWidgets.QToolButton()
        self.b_layer_adv.setText("⚙")
        self.b_layer_adv.setToolTip(
            "Advanced sorting: track SEVERAL layers at once.\n"
            "ANY = outdated as soon as one of them moved.\n"
            "ALL = outdated only when they all moved.\n"
            "A layer a shot doesn't consume is ignored for that shot."
        )
        self.b_layer_adv.clicked.connect(self._open_layer_filter)
        top.addWidget(self.b_layer_adv)
        # message discret : ce qui a ete ignore, et pourquoi (jamais tu, jamais bruyant)
        self.lbl_ignored = QtWidgets.QLabel("")
        self.lbl_ignored.setStyleSheet("color: %s;" % theme_colors(self)["gray"])
        top.addWidget(self.lbl_ignored)
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
        wlay.addLayout(top)

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

        # --- MODE DE SAUVEGARDE de la scene : une decision PAR RUN, a cote du bouton ---
        # Pas dans les Settings : on doit la voir au moment de cliquer. "Leave untouched"
        # evite de creer une vNNN+1 dans la chaine d'un autre (un lighter qui sauve
        # par-dessus sa version tomberait le lendemain sur la notre, sans son travail).
        save_row = QtWidgets.QHBoxLayout()
        save_row.addStretch(1)
        save_row.addWidget(QtWidgets.QLabel("Scene:"))
        self.save_group = QtWidgets.QButtonGroup(self)
        self.save_group.setExclusive(True)
        self.b_save_ver = QtWidgets.QPushButton("Version-up")
        self.b_save_keep = QtWidgets.QPushButton("Leave untouched")
        for b, mode, tip in (
            (
                self.b_save_ver,
                SAVE_VERSION_UP,
                "Publish the caches AND save a new scene version.\n"
                "Use it when nobody else is working in this scene.",
            ),
            (
                self.b_save_keep,
                SAVE_LEAVE,
                "Publish the caches only. The scene file is NOT written, so nobody's\n"
                "version chain changes. Renders are still submitted, with a comment\n"
                "saying the scene was not saved.",
            ),
        ):
            b.setCheckable(True)
            b.setToolTip(tip)
            b.setProperty("save_mode", mode)
            self.save_group.addButton(b)
            save_row.addWidget(b)
        self.save_group.buttonClicked.connect(self._on_save_mode_changed)
        # scene Maya : QUELS exports lancer apres la mise a jour (defaut = ceux coches
        # dans le State Manager de la scene). Invisible pour une scene Houdini.
        save_row.addSpacing(18)
        self.lbl_exports = QtWidgets.QLabel("Exports:")
        save_row.addWidget(self.lbl_exports)
        self.b_exports = QtWidgets.QPushButton("")
        self.b_exports.clicked.connect(self._open_exports_dialog)
        save_row.addWidget(self.b_exports)
        # scene Houdini avec des LOP_Render : reglages ferme des renders soumis (frames,
        # prio, chunk, pool...). Invisible sans render.
        self.lbl_farm = QtWidgets.QLabel("Farm:")
        save_row.addWidget(self.lbl_farm)
        self.b_farm = QtWidgets.QPushButton("")
        self.b_farm.clicked.connect(self._open_farm_dialog)
        save_row.addWidget(self.b_farm)
        save_row.addStretch(1)
        top_lay.addLayout(save_row)
        self.lbl_save_mode = QtWidgets.QLabel("")
        self.lbl_save_mode.setAlignment(Qt.AlignCenter)
        self.lbl_save_mode.setStyleSheet("color: %s;" % theme_colors(self)["gray"])
        top_lay.addWidget(self.lbl_save_mode)
        self._apply_save_mode(self.cfg.get("save_mode", SAVE_VERSION_UP))

        act = QtWidgets.QHBoxLayout()
        act.addStretch(1)
        self.b_apply = QtWidgets.QPushButton(APPLY_LABEL)
        self.b_apply.setToolTip(
            "For each ticked shot: bump the import to the latest version and re-cache.\n"
            "The scene is then version-upped OR left untouched (see 'Scene' above).\n"
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

        wlay.addWidget(top_w, 1)

        # --- panneau de scenes a gauche, TOUJOURS ouvert (remplace 'Choose scene...') ---
        self.browser = SceneBrowser()
        self.browser.setMinimumWidth(360)  # 3 colonnes lisibles
        self.browser.sceneChosen.connect(self._on_browser_scene)
        self.hsplit = QtWidgets.QSplitter(Qt.Horizontal)
        self.hsplit.addWidget(self.browser)
        self.hsplit.addWidget(work)
        self.hsplit.setChildrenCollapsible(False)
        # la fenetre s'agrandit -> c'est la table qui en profite, pas le panneau
        self.hsplit.setStretchFactor(0, 0)
        self.hsplit.setStretchFactor(1, 1)
        bw = self._browser_width()
        self.hsplit.setSizes([bw, max(600, self.width() - bw)])
        self.hsplit.splitterMoved.connect(self._on_hsplit_moved)

        self.split = QtWidgets.QSplitter(Qt.Vertical)
        self.split.addWidget(self.hsplit)
        self.split.addWidget(self.log)
        self.split.setChildrenCollapsible(False)
        self.split.setStretchFactor(0, 3)
        self.split.setStretchFactor(1, 2)
        self.split.setSizes([580, 300])
        lay.addWidget(self.split, 1)

        self.status = self.statusBar()
        self.progress = QtWidgets.QProgressBar()
        self.progress.setMaximumWidth(220)
        self.progress.setTextVisible(True)
        self.progress.hide()
        self.status.addPermanentWidget(self.progress)
        self.status.showMessage(
            "Ready. Pick a scene on the left, then 'Load Scene (slow)' — or "
            "'Reload (fast)' if it was already loaded once."
        )

    def _set_headers(self):
        layer = self._layer_display_name()
        labels = ["Shot", layer, "State", "SOP caches", "Renders", "Caches"]
        tips = [
            "Prism shot (sequence/shot), resolved from the cache output",
            "Tracked layer(s): consumed -> latest (drives OUTDATED). With several "
            "layers the cell shows how many are stale; hover for the detail. "
            "Pick '%s' to follow the shot container." % STACK_LABEL,
            "OUTDATED / up to date / n/a / ERROR",
            "FX only: SOP caches re-simulated before publish (checked/total). "
            "Click to choose which caches to re-sim. Blank = cfx (no SOP chain).",
            "Lighting only: layers (render executions) rendered on the FARM when the "
            "shot is ticked (checked/total). Ticking the shot = re-cache THEN render "
            "these layers. Click to choose which layers; default = enabled on the node. "
            "Blank = no render node on this shot.",
            "USD caches (prism::lop_filecache) re-cached when the shot is ticked "
            "(checked/total). Click to choose which ones -- a shot can have "
            "several, publishing different products. Unticking all = no re-cache.",
        ]
        self.table.setHorizontalHeaderLabels(labels)
        for i, tip in enumerate(tips):
            self.table.horizontalHeaderItem(i).setToolTip(tip)

    # -------------------------------------------------------------- helpers
    def _pick_hip(self):
        start = os.path.dirname(self.ed_hip.text()) or ""
        p, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Scene (.hip / .ma)",
            start,
            "Scenes (*.hip *.hipnc *.hiplc *.ma);;Houdini (*.hip *.hipnc *.hiplc);;"
            "Maya ASCII (*.ma)",
        )
        if p:
            self.ed_hip.setText(p)

    # ------------------------------------------------ "From scene" (Houdini)
    @staticmethod
    def _houdini_scene():
        """La scene ouverte dans Houdini quand le shelf a lance l'outil (env posee par
        houdini_shelf_tool.py), '' si l'outil n'a pas ete lance depuis Houdini."""
        p = os.environ.get(ENV_HIP, "")
        return p if p and os.path.isfile(p) else ""

    def _refresh_from_scene_button(self):
        hip = self._houdini_scene()
        self.b_from_scene.setEnabled(bool(hip))
        self.b_from_scene.setToolTip(
            (
                "Use the scene open in Houdini:\n%s\n(the one open when this window was "
                "launched from the shelf)" % hip
            )
            if hip
            else "Launch the tool from the Houdini shelf to use the scene you have open."
        )

    def _use_houdini_scene(self):
        hip = self._houdini_scene()
        if not hip:
            self._refresh_from_scene_button()
            return
        self.ed_hip.setText(hip)
        self.status.showMessage("Scene set from Houdini: %s" % os.path.basename(hip))

    ENTITY_DIRS = ("Shots", "Assets")

    @staticmethod
    def _is_prism_shots(d, kinds=ENTITY_DIRS):
        """Vraie racine d'entites Prism : dossier 'Shots' ou 'Assets' dont le parent est
        '03_Production', OU dont le projet (parent du parent) contient
        00_Pipeline/pipeline.json. Evite de detourner un dossier homonyme (ex archive)
        -> picker peuple mais faux."""
        if not d or not os.path.isdir(d) or os.path.basename(d) not in kinds:
            return False
        parent = os.path.dirname(d)
        if os.path.basename(parent) == "03_Production":
            return True
        proj = os.path.dirname(parent)
        return os.path.isfile(os.path.join(proj, "00_Pipeline", "pipeline.json"))

    @staticmethod
    def _find_shots_up(path):
        """Remonte depuis `path` jusqu'a la 1ere racine d'entites Prism ('Shots' OU
        'Assets' : une scene multi-shots peut etre rangee sous Assets). '' si aucune."""
        p = path
        while p:
            if os.path.basename(p) in Main.ENTITY_DIRS and Main._is_prism_shots(p):
                return p
            nxt = os.path.dirname(p)
            if nxt == p:
                return ""
            p = nxt
        return ""

    def _entity_roots(self):
        """{'Shots': chemin, 'Assets': chemin} du projet courant (les deux existent
        rarement a moitie, mais on ne propose que ce qui existe)."""
        base = self._shots_root()
        if not base:
            return {}
        prod = os.path.dirname(base)  # .../03_Production
        out = {}
        for kind in self.ENTITY_DIRS:
            d = os.path.join(prod, kind)
            if os.path.isdir(d):
                out[kind] = d
        return out

    @staticmethod
    def _resolve_shots_root(d):
        """Depuis un dossier CHOISI, localise le 'Shots' Prism : le dossier lui-meme,
        <d>/03_Production/Shots, <d>/Shots, ou en remontant (cas ou l'artiste a pointe
        un dossier de scene profond). '' si rien de coherent."""
        if not d or not os.path.isdir(d):
            return ""
        if Main._is_prism_shots(d):
            return d
        subs = []
        for kind in Main.ENTITY_DIRS:
            subs += [os.path.join(d, "03_Production", kind), os.path.join(d, kind)]
        for sub in subs:
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

    # ------------------------------------------ panneau de scenes (gauche)
    def _on_browser_scene(self, path):
        """Clic sur une scene du panneau : elle va dans le champ, comme avec 'Browse...'
        (tout le reste suit via _on_hip_changed)."""
        if path and path != self.ed_hip.text().strip():
            self.ed_hip.setText(path)

    def _sync_browser(self):
        """Le panneau suit le projet et la scene du champ, sans rien recharger. Shots
        ET Assets : une scene multi-shots peut etre rangee cote Assets."""
        roots = self._entity_roots()
        # dernier recours de _shots_root (aucun projet ni scene) : le dernier projet vu
        shots = roots.get("Shots") or roots.get("Assets")
        if shots and shots != self.settings.value("shots_root", ""):
            self.settings.setValue("shots_root", shots)
        self.browser.set_roots(roots)
        self.browser.select_path(self.ed_hip.text().strip())

    def _browser_width(self):
        """Largeur du panneau memorisee (par utilisateur), bornee. Defaut = les 3
        colonnes (Sequence/Shot | Department | Task) lisibles sans les elargir."""
        try:
            w = int(self.settings.value("browser_width", 580))
        except (TypeError, ValueError):
            w = 580
        return max(420, min(w, 1100))

    def _on_hsplit_moved(self, *_):
        self.settings.setValue("browser_width", self.hsplit.sizes()[0])

    # --------------------------------------- presets de scene (par projet)
    def _refresh_presets_button(self, prj, presets=None):
        """Nombre de presets dans le bouton. Le json n'est relu que si le projet a
        change : _on_hip_changed tourne a chaque frappe dans le champ."""
        if presets is None:
            if prj == self._presets_prj:
                return
            presets = read_presets(prj) if prj else []
        self._presets_prj = prj
        n = len(presets)
        self.b_presets.setText("★ Presets (%d)" % n if n else "★ Presets")
        self.b_presets.setToolTip(
            "Scenes saved for everyone on %s: one click loads their LATEST version.\n"
            "'Save current scene as preset...' adds the scene of the field."
            % project_name_of(prj)
            if prj
            else "Pick a project first: presets are shared per project."
        )

    def _fill_presets_menu(self):
        """Relu a CHAQUE ouverture : un preset enregistre par un collegue apparait tout
        de suite, sans relancer l'outil."""
        m = self.presets_menu
        m.clear()
        prj = self._project()
        if not prj:
            m.addAction("No project selected/detected").setEnabled(False)
            return
        presets = read_presets(prj)
        self._refresh_presets_button(prj, presets)
        if not presets:
            m.addAction("No preset on %s yet" % project_name_of(prj)).setEnabled(False)
        for p in presets:
            a = m.addAction(p["name"])
            a.setToolTip(
                "%s  ·  %s (latest version)\nsaved by %s, %s"
                % (
                    preset_where(p),
                    p["scene"],
                    p.get("created_by") or "?",
                    p.get("created_at") or "?",
                )
            )
            a.triggered.connect(lambda _=False, p=p: self._load_preset(p))
        m.addSeparator()
        save = m.addAction("Save current scene as preset...")
        save.setEnabled(self._preset_candidate() is not None)
        save.triggered.connect(self._save_preset)
        if presets:
            dm = self.presets_delete_menu
            dm.clear()
            for p in presets:
                a = dm.addAction(p["name"])
                a.triggered.connect(lambda _=False, p=p: self._delete_preset(p))
            m.addMenu(dm)

    def _preset_candidate(self):
        """(projet, scene) si le champ montre une scene DU projet courant, sinon None."""
        prj = self._project()
        scene = self.ed_hip.text().strip()
        if (
            not prj
            or not os.path.isfile(scene)
            or not scene.lower().endswith(PICKER_EXT)
        ):
            return None
        try:
            make_preset(prj, "", scene, "")
        except ValueError:
            return None
        return prj, scene

    def _load_preset(self, preset):
        """La DERNIERE version de la scene du preset va dans le champ ; le reste suit
        comme pour un clic dans le panneau."""
        prj = self._project()
        scene = preset_scene(prj, preset) if prj else ""
        if not scene:
            QtWidgets.QMessageBox.warning(
                self,
                "Preset",
                "Preset '%s': no '%s' scene left in\n%s\n\nIt was probably renamed or "
                "moved: delete the preset and save it again."
                % (
                    preset["name"],
                    preset["scene"],
                    preset_task_dir(prj, preset) if prj else "?",
                ),
            )
            return
        self.ed_hip.setText(scene)

    def _save_preset(self):
        cand = self._preset_candidate()
        if cand is None:
            QtWidgets.QMessageBox.information(
                self, "Preset", "Pick a scene of the project first (left panel)."
            )
            return
        prj, scene = cand
        name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Save scene preset",
            "Preset name, shared with everyone on %s.\n"
            "It always opens the LATEST version of %s."
            % (project_name_of(prj), scene_family(scene)),
            text=scene_family(scene),
        )
        name = (name or "").strip()
        if not ok or not name:
            return
        # relu juste avant d'ecrire : un collegue a pu en ajouter un entre-temps
        presets = read_presets(prj)
        new = make_preset(prj, name, scene, os.environ.get("USERNAME") or "?")
        same = [i for i, p in enumerate(presets) if p["name"].lower() == name.lower()]
        if same:
            yes = QtWidgets.QMessageBox.StandardButton.Yes
            msg = "A preset '%s' already exists on %s. Replace it?" % (
                presets[same[0]]["name"],
                project_name_of(prj),
            )
            if QtWidgets.QMessageBox.question(self, "Preset", msg) != yes:
                return
            presets[same[0]] = new  # garde sa place dans le menu
        else:
            presets.append(new)
        if self._write_presets(prj, presets):
            self.status.showMessage(
                "Preset '%s' saved for everyone on %s." % (name, project_name_of(prj))
            )

    def _delete_preset(self, preset):
        prj = self._project()
        if not prj:
            return
        yes = QtWidgets.QMessageBox.StandardButton.Yes
        msg = (
            "Delete the preset '%s' for everyone on %s?\n(the scene is not touched)"
            % (
                preset["name"],
                project_name_of(prj),
            )
        )
        if QtWidgets.QMessageBox.question(self, "Preset", msg) != yes:
            return
        name = preset["name"].lower()
        presets = [p for p in read_presets(prj) if p["name"].lower() != name]
        if self._write_presets(prj, presets):
            self.status.showMessage("Preset '%s' deleted." % preset["name"])

    def _write_presets(self, prj, presets):
        try:
            write_presets(prj, presets)
        except Exception as ex:
            QtWidgets.QMessageBox.warning(
                self,
                "Preset",
                "Couldn't write the presets:\n%s\n\n%s" % (presets_path(prj), ex),
            )
            return False
        self._refresh_presets_button(prj, presets)
        return True

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
        self._cache_selection = {}
        self._export_selection = None
        if self._farm_overrides and self._farm_for != self._scene_key():
            self._farm_overrides = {}  # reglages ferme decides pour une AUTRE scene
        prj = self._project()
        self._refresh_presets_button(prj)
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
        self._sync_browser()
        self._apply_kind(scene_kind(self.ed_hip.text().strip()))
        if self._kind == "maya":
            self._read_maya_scene()  # lecture texte du .ma : instantane, sans Maya
            return
        self._refresh_layers()
        self._maybe_preview()  # affichage instantane depuis le json si dispo

    # ------------------------------------------------ type de scene (Houdini / Maya)
    def _is_maya(self):
        return self._kind == "maya"

    def _apply_kind(self, kind):
        """Adapte la fenetre au type de scene. Houdini : shots / layers suivis / caches /
        renders (inchange). Maya : une ligne par RIG reference + les exports de la scene.
        On masque ce qui n'a pas de sens plutot que de le griser : rien a comprendre."""
        kind = kind or "houdini"  # champ vide / en cours de saisie -> vue historique
        if kind == self._kind:
            return
        changed = self._kind is not None
        self._kind = kind
        maya = kind == "maya"
        for w in (self.lbl_layer, self.combo_layer, self.b_layer_adv, self.lbl_ignored):
            w.setVisible(not maya)
        self.b_load.setVisible(not maya)  # une scene Maya se lit en texte : instantane
        self.lbl_exports.setVisible(maya)
        self.b_exports.setVisible(maya)
        self.b_reload.setToolTip(
            "Re-read the rigs of the .ma and the latest published versions "
            "(no Maya, instant)."
            if maya
            else "Re-check the version gaps by reading the DISK only (no Houdini, "
            "instant).\nUses the last known state of the scene's nodes + scans the "
            "latest versions.\nDoesn't see node changes made in Houdini since -> use "
            "'Load Scene (slow)'."
        )
        self.b_check.setToolTip(
            "Tick every rig flagged OUTDATED."
            if maya
            else "Tick every shot flagged OUTDATED."
        )
        self.b_apply.setToolTip(
            "For each ticked rig: swap its references to the latest version, check that "
            "no animation was lost,\nthen version-up the scene OR leave it untouched "
            "(see 'Scene' above), then run the ticked exports."
            if maya
            else "For each ticked shot: bump the import to the latest version and "
            "re-cache.\nThe scene is then version-upped OR left untouched (see 'Scene' "
            "above).\nLighting shots also get RE-RENDERED on the farm (their ticked "
            "layers)."
        )
        if changed:  # les lignes de l'autre type de scene ne veulent plus rien dire
            self._data = []
            self._maya_rigs = []
            self._maya_exports = []
            self._maya_read = None
            self._previewed = None
            self._populating = True
            try:
                self.table.setRowCount(0)
            finally:
                self._populating = False
            self._set_badge("")
        if maya:
            self.table.setColumnCount(4)
            self._set_headers_maya()
        else:
            self.table.setColumnCount(6)
            self._set_headers()
        self._apply_save_mode(self._save_mode())  # le texte de consequence change
        self._update_farm_button()
        self._update_apply_count()

    def _set_headers_maya(self):
        labels = ["Rig", "Version", "State", "References"]
        tips = [
            "Asset whose rig the scene references (category/asset). Tick it to update.",
            "Rig version used by the scene -> latest published version.",
            "OUTDATED when a newer rig version is published.",
            "How many times the scene references this rig (namespaces in the tooltip). "
            "They are all swapped together.",
        ]
        self.table.setHorizontalHeaderLabels(labels)
        for i, tip in enumerate(tips):
            self.table.horizontalHeaderItem(i).setToolTip(tip)

    def _read_maya_scene(self, preserve=False, force=False):
        """Rigs + exports de la scene .ma, lus dans le TEXTE du fichier (tete du .ma) :
        instantane, sans Maya ni licence. Les dernieres versions viennent du disque."""
        scene = self.ed_hip.text().strip()
        if not os.path.isfile(scene):
            return
        try:
            key = (scene, os.path.getmtime(scene))
        except Exception:
            key = (scene, None)
        if key == self._maya_read and not force:
            return
        self._maya_read = key
        if not maya_refs.is_ascii_maya(scene):
            self._maya_rigs, self._maya_exports = [], []
            self._populate_maya([], preserve)
            self.status.showMessage(
                "This Maya scene isn't ASCII (.mb?): its rigs can't be read without Maya."
            )
            return
        QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            rigs = maya_refs.rig_status(scene)
            exports = maya_refs.scene_exports(scene)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        self._maya_rigs, self._maya_exports = rigs, exports
        self._populate_maya(rigs, preserve)
        self._set_badge("maya")
        n_out = sum(1 for r in rigs if r.get("stale"))
        self.status.showMessage(
            "%d rig(s)  -  %d outdated  -  %d export state(s)  (read from the .ma, "
            "no Maya)." % (len(rigs), n_out, len(exports))
            if rigs
            else "No Prism rig reference found in this scene."
        )

    def _populate_maya(self, rigs, preserve=False):
        """Une ligne par rig. Meme regle de cases que les shots : cochee si OUTDATED, sauf
        `preserve` (re-lecture de la meme scene) ou on garde la selection de l'artiste."""
        prev = {}
        if preserve:
            for r in range(self.table.rowCount()):
                it = self.table.item(r, 0)
                if it is not None:
                    prev[it.data(Qt.UserRole)] = it.checkState() == Qt.Checked
        self._populating = True
        try:
            self._set_headers_maya()
            self.table.setRowCount(0)
            col = theme_colors(self)
            for d in rigs:
                r = self.table.rowCount()
                self.table.insertRow(r)
                stale = bool(d.get("stale"))
                missing = d.get("missing") or []
                it0 = QtWidgets.QTableWidgetItem(
                    rig_label(d.get("id", "")) + ("  ⚠" if missing else "")
                )
                it0.setData(Qt.UserRole, d.get("id", ""))
                it0.setFlags(it0.flags() | Qt.ItemIsUserCheckable)
                was = prev.get(d.get("id", ""))
                ticked = stale if was is None else was
                it0.setCheckState(Qt.Checked if ticked else Qt.Unchecked)
                it0.setToolTip(
                    "%s  (%s)\n%s"
                    % (
                        d.get("asset"),
                        d.get("product"),
                        (d.get("refs") or [{}])[0].get("path", ""),
                    )
                )
                self.table.setItem(r, 0, it0)
                if d.get("latest") is None:
                    state = "? (no published version found)"
                else:
                    state = STATE_TEXT["outdated" if stale else "uptodate"]
                if missing:  # la version utilisee a ete supprimee du disque
                    state += " · file missing"
                namespaces = [
                    x.get("ns") or x.get("refnode") or "?" for x in d.get("refs") or []
                ]
                vals = [
                    self._pair(d.get("version"), d.get("latest")),
                    state,
                    "%d" % (d.get("n_refs") or len(namespaces)),
                ]
                for c, v in enumerate(vals, start=1):
                    cell = QtWidgets.QTableWidgetItem(str(v))
                    if c == 2 and missing:
                        cell.setToolTip(
                            "The rig version this scene references no longer exists on "
                            "disk:\n%s\nMaya opens the scene with an empty reference; "
                            "updating to the latest version repairs it."
                            % "\n".join(missing)
                        )
                    if c == 3:
                        cell.setToolTip("\n".join(namespaces))
                    self.table.setItem(r, c, cell)
                if stale:
                    for c in range(self.table.columnCount()):
                        self.table.item(r, c).setBackground(col["bg_outdated"])
            self.table.resizeColumnsToContents()
        finally:
            self._populating = False
        self._update_exports_button()
        self._update_apply_count()

    # ------------------------------------------------ exports d'une scene Maya
    def _export_sel(self):
        """uuids des exports a lancer. Source = json partage a cote de la scene (choix
        explicite de l'artiste), sinon les states coches dans le State Manager de la
        scene. Un uuid qui n'existe plus dans la scene est ignore."""
        known = [e["uuid"] for e in self._maya_exports]
        if self._export_selection is None:
            self._ensure_store()
            saved = self._fx_store.get("export_states")
            if isinstance(saved, list):
                self._export_selection = [u for u in known if u in set(saved)]
            else:
                self._export_selection = [
                    e["uuid"] for e in self._maya_exports if e.get("enabled")
                ]
        keep = set(self._export_selection)
        return [u for u in known if u in keep]

    def _update_exports_button(self):
        exports = self._maya_exports
        sel = set(self._export_sel()) if exports else set()
        if not exports:
            self.b_exports.setText("none in this scene")
            self.b_exports.setEnabled(False)
            self.b_exports.setToolTip("This scene has no Prism export state.")
        else:
            self.b_exports.setEnabled(self.proc is None)
            self.b_exports.setText("%d/%d  ▸" % (len(sel), len(exports)))
            self.b_exports.setToolTip(
                "Prism exports run after the update (click to choose):\n"
                + "\n".join(
                    "%s %s  →  %s"
                    % ("x" if e["uuid"] in sel else " ", e["name"], e["product"] or "?")
                    for e in exports
                )
            )
        self._apply_save_mode(self._save_mode())  # 'dry run' depend des exports coches

    def _open_exports_dialog(self):
        if not self._maya_exports:
            return
        name = os.path.basename(self.ed_hip.text().strip())
        dlg = ExportPickerDialog(
            self, name, self._maya_exports, set(self._export_sel())
        )
        ok = dlg.exec() if hasattr(dlg, "exec") else dlg.exec_()
        if not ok:
            return
        self._export_selection = dlg.checked_uuids()
        self._ensure_store()
        self._fx_store["export_states"] = list(self._export_selection)
        self._save_hip_store()  # partage : le prochain qui ouvre la scene a le meme choix
        self._update_exports_button()

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

    # ------------------------------------------------ layers suivis (multi + OU/ET)
    def _tracked(self):
        """Layers suivis. Toujours au moins un : une liste vide ne voudrait rien dire
        (on ne saurait plus sur quoi juger la peremption)."""
        lst = as_layer_list(self.cfg.get("tracked_layers"))
        return (
            lst or as_layer_list(self.cfg.get("tracked_layer")) or ["_layer_anm_master"]
        )

    def _layer_mode(self):
        return "and" if self.cfg.get("tracked_mode") == "and" else "or"

    def _pretty_layer(self, layer):
        if layer == STACK_LAYER:
            return STACK_LABEL
        for name, lay in self._departments:
            if lay == layer:
                return name.split("  (")[0]
        return layer.replace("_layer_", "").replace("_master", "") or "Layer"

    def _refresh_layers(self):
        """Remplit le dropdown depuis les layers que la scene consomme REELLEMENT.

        /!\ On ne retombe PLUS sur `usd.departmentOrder` de pipeline.json : il liste
        41 departements sur yuka_2604 (deux generations de nommage cote a cote, plus
        des collisions de casse fx/FX, cfx/CFX), alors qu'une stack de shot en compte 2
        a 8. Le dropdown en devenait illisible. Sans scene chargee, on n'affiche que le
        layer memorise -- ce qui est propose EXISTE."""
        depts = self._layers_in_data()
        if not depts:
            depts = [(self._pretty_layer(x), x) for x in self._tracked()]
        self._departments = depts
        sel = self._tracked()
        self.combo_layer.blockSignals(True)
        self.combo_layer.clear()
        # plusieurs layers suivis (roue crantee) -> une entree de synthese en tete :
        # le dropdown ne peut pas mentir en n'en montrant qu'un.
        if len(sel) > 1:
            self.combo_layer.addItem(self._layer_display_name(), None)
        idx = 0
        for name, layer in depts:
            ready = "(" in name or name == STACK_LABEL
            self.combo_layer.addItem(
                name if ready else "%s  (%s)" % (name, layer), layer
            )
            if len(sel) == 1 and layer == sel[0]:
                idx = self.combo_layer.count() - 1
        self.combo_layer.setCurrentIndex(idx)
        self.combo_layer.blockSignals(False)
        self._set_headers()

    # ------------------------------------------------ sauvegarde de la scene (par run)
    def _save_mode(self):
        return (
            SAVE_LEAVE if self.cfg.get("save_mode") == SAVE_LEAVE else SAVE_VERSION_UP
        )

    def _apply_save_mode(self, mode):
        """Coche le bon bouton et met la ligne de consequence a jour. La consequence est
        affichee AVANT le clic : on doit savoir ce qui va arriver a la scene."""
        mode = SAVE_LEAVE if mode == SAVE_LEAVE else SAVE_VERSION_UP
        self.cfg["save_mode"] = mode
        (self.b_save_keep if mode == SAVE_LEAVE else self.b_save_ver).setChecked(True)
        self.lbl_save_mode.setText(self._save_mode_text(mode))

    def _save_mode_text(self, mode):
        """Ligne de consequence sous le switch, selon le type de scene. Maya + 'Leave
        untouched' sans aucun export = rien n'est ecrit : on le dit (dry run)."""
        if not self._is_maya():
            return SAVE_MODE_TEXT[mode]
        if mode == SAVE_LEAVE and self._maya_exports and not self._export_sel():
            return SAVE_LEAVE_DRY_RUN
        return SAVE_MODE_TEXT_MAYA[mode]

    def _save_mode_summary(self, ids, has_renders):
        """Ce qui VA et ne va PAS arriver a la scene, pour la confirmation. Les
        consequences d'un 'Leave untouched' sont dites, pas devinees apres coup."""
        if self._save_mode() == SAVE_VERSION_UP:
            return "Scene: a NEW version will be saved (version-up)."
        lines = [
            "Scene: LEFT UNTOUCHED - the .hip is not written, nobody's versions change."
        ]
        if has_renders:
            lines.append(
                "Renders: submitted with the comment '(scene not saved)' - their source "
                "scene won't contain this update."
            )
        idset = set(ids)
        pinned = [
            d.get("shot", "?")
            for d in self._data
            if d.get("id") in idset
            and "lop_import" in (d.get("import_type") or "").lower()
        ]
        if pinned:
            lines.append(
                "Pinned imports (%d shot(s): %s): their scene keeps the OLD USD path. "
                "The published cache is up to date, but a manual re-cache from that "
                "scene would go back to the old stack."
                % (
                    len(pinned),
                    ", ".join(pinned[:4]) + ("..." if len(pinned) > 4 else ""),
                )
            )
        return "\n".join(lines)

    def _on_save_mode_changed(self, button):
        self._apply_save_mode(button.property("save_mode"))
        self._save_settings()  # memorise PAR UTILISATEUR (QSettings), pas dans le sidecar

    def _on_layer_changed(self):
        """Choix dans le dropdown = UN layer suivi (on retombe du multi vers le simple)."""
        layer = self.combo_layer.currentData()
        if not layer or [layer] == self._tracked():
            return
        self.cfg["tracked_layers"] = [layer]
        self.cfg["tracked_layer"] = layer
        self._commit_layers(
            "Tracked: %s (no reload needed)." % self._layer_display_name()
        )

    def _open_layer_filter(self):
        """Roue crantee : suivre PLUSIEURS layers, en ANY (OU) ou ALL (ET)."""
        if not self._departments:
            self._refresh_layers()
        dlg = LayerFilterDialog(
            self, self._departments, self._tracked(), self._layer_mode()
        )
        ok = dlg.exec() if hasattr(dlg, "exec") else dlg.exec_()
        if not ok:
            return
        sel, mode = dlg.result_layers(), dlg.result_mode()
        if not sel:  # garde-fou : sans layer suivi, plus rien n'est jugeable
            self.status.showMessage("Keep at least one tracked layer.")
            return
        if sel == self._tracked() and mode == self._layer_mode():
            return
        self.cfg["tracked_layers"] = sel
        self.cfg["tracked_layer"] = sel[0]  # forme historique, gardee a jour
        self.cfg["tracked_mode"] = mode
        self._commit_layers(
            "Tracked: %s (no reload needed)." % self._layer_display_name()
        )

    def _commit_layers(self, msg):
        """Applique un changement de layers/mode : settings, json partage, re-rendu.
        Le moteur envoie TOUS les layers -> recalcul instantane, sans recharger."""
        self._save_settings()
        if self._hip_sidecar_path():
            self._save_hip_store()
        self._refresh_layers()
        if self._data:
            self._populate(self._data, preserve=True)
        self.status.showMessage(msg)

    def _apply_saved_layer(self):
        """Applique les layers suivis du json partage (forme liste, ou l'ancienne forme
        mono-layer), sans recharger la scene ni re-populer (fait juste apres)."""
        self._ensure_store()
        saved = as_layer_list(self._fx_store.get("tracked_layers")) or as_layer_list(
            self._fx_store.get("tracked_layer")
        )
        mode = self._fx_store.get("tracked_mode") or self._layer_mode()
        if not saved or (saved == self._tracked() and mode == self._layer_mode()):
            return
        self.cfg["tracked_layers"] = saved
        self.cfg["tracked_layer"] = saved[0]
        self.cfg["tracked_mode"] = "and" if mode == "and" else "or"
        self._refresh_layers()

    def _layer_display_name(self):
        """Libelle court des layers suivis (bouton + entete de colonne). Le separateur
        DIT le mode : ' / ' pour OU, ' & ' pour ET -- pas besoin d'un 2e widget."""
        sel = self._tracked()
        names = [self._pretty_layer(x) for x in sel]
        if len(names) == 1:
            return names[0]
        joined = (" & " if self._layer_mode() == "and" else " / ").join(names)
        if len(joined) <= 34:
            return joined
        return "%d layers (%s)" % (
            len(names),
            "ALL" if self._layer_mode() == "and" else "ANY",
        )

    def _open_settings(self):
        dlg = SettingsDialog(self, dict(self.cfg))
        ok = dlg.exec() if hasattr(dlg, "exec") else dlg.exec_()
        if getattr(dlg, "reset_requested", False):
            self._reset_local_settings()
            return
        if ok:
            self.cfg.update(dlg.values())
            self.cfg["hython"] = detect_hython(self.cfg.get("hython"))
            self.cfg["mayapy"] = detect_mayapy(self.cfg.get("mayapy"))
            self._save_settings()
            self._on_hip_changed()

    def _reset_local_settings(self):
        """Efface TOUTES les prefs QSettings (scenes, projet, selections SOP, hython...)
        et recharge les defauts. Repart d'une machine 'propre'."""
        self.settings.clear()
        self.settings.sync()
        self._fx_selection = {}
        self._render_selection = {}
        self._cache_selection = {}
        self._fx_store = None  # le json partage (a cote du hip) N'est PAS efface
        self._data = []
        self._maya_rigs, self._maya_exports = [], []
        self._maya_read = None
        self._export_selection = None
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
        self.b_layer_adv.setEnabled(not on)
        self.b_save_ver.setEnabled(not on)  # le mode ne change pas en cours de run
        self.b_save_keep.setEnabled(not on)
        self.b_exports.setEnabled(not on and bool(self._maya_exports))
        self.b_farm.setEnabled(not on)
        # changer de scene en plein run melangerait les resultats (sidecar, scene
        # sauvee) : le panneau et les presets se figent avec le reste
        self.browser.setEnabled(not on)
        self.b_presets.setEnabled(not on)
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
        # layers suivis : un --tracked-layer PAR layer + le mode, pour que le
        # moteur juge EXACTEMENT comme le tableau (surtout le statut re-emis
        # apres un apply, sinon la table changerait de sens juste apres).
        for lay in self._tracked():
            args += ["--tracked-layer", lay]
        args += ["--tracked-mode", self._layer_mode()]
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

    # ---------------------------------------------------------- moteur Maya
    def _maya_env(self):
        """Environnement de mayapy : celui du poste, SANS ce qui vient de Houdini (l'UI est
        lancee depuis le shelf Houdini : son PYTHONPATH/PATH pointent le python et
        l'integration Prism de Houdini, qui masqueraient ceux de Maya -- meme python
        3.11 des deux cotes) ni du venv de l'UI. Le PYTHONPATH studio de Maya vient de
        Maya.env (MAYA_ENV_DIR), que mayapy relit lui-meme (verifie)."""
        env = QProcessEnvironment.systemEnvironment()
        venv = os.path.normcase(os.path.abspath(sys.prefix))

        def _foreign(entry):
            e = os.path.normcase(os.path.abspath(entry))
            return (
                self._houdini_build(entry) is not None  # une install Houdini
                or "\\plugins\\houdini" in e  # integration Prism Houdini
                or e.startswith(venv)  # le venv de l'UI
            )

        for var in ("PATH", "PYTHONPATH"):
            val = env.value(var, "")
            if val:
                kept = [p for p in val.split(os.pathsep) if p and not _foreign(p)]
                env.insert(var, os.pathsep.join(kept))
        for var in (
            "PYTHONHOME",
            "VIRTUAL_ENV",
            "QT_PLUGIN_PATH",
            "QT_QPA_PLATFORM_PLUGIN_PATH",
            "QML2_IMPORT_PATH",
        ):
            env.remove(var)
        env.insert(
            "PYTHONIOENCODING", "utf-8"
        )  # logs Prism accentues : pas de crash cp1252
        env.insert("PYTHONUNBUFFERED", "1")  # le log arrive en direct, pas a la fin
        return env

    def _start_maya(self, extra_args):
        """Lance recache_maya.py dans mayapy (update -> verif -> save -> exports)."""
        if self.proc is not None:
            return
        mp = self.cfg.get("mayapy", "")
        scene = self.ed_hip.text().strip()
        if not mp or not os.path.exists(mp):
            QtWidgets.QMessageBox.warning(
                self, "mayapy", "mayapy not found (see Settings):\n%s" % mp
            )
            return
        if not scene or not os.path.isfile(scene):
            QtWidgets.QMessageBox.warning(self, "Scene", "No .ma found:\n%s" % scene)
            return
        if not self._project():
            QtWidgets.QMessageBox.warning(
                self, "Project", "Prism project not found from this scene."
            )
            return
        self._save_settings()
        self._buf = ""
        self._linebuf = ""
        self._in_status = False
        self._mode = "maya_apply"
        self._run_scene = scene
        args = [ENGINE_MAYA, "--scene", scene, "--project", self._project()]
        args += extra_args
        self.log.appendPlainText("\n$ %s %s\n" % (mp, " ".join(args)))
        self.proc = QProcess(self)
        self.proc.setProcessEnvironment(self._maya_env())
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._on_out)
        self.proc.finished.connect(self._on_finished)
        self.proc.start(mp, args)
        self.progress.setRange(0, 0)
        self.progress.show()
        self._prog_shot = ""
        self._busy(True)
        self._start_ticker("Starting Maya…")

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
        unit = "rig" if self._mode == "maya_apply" else "shot"
        for m in re.finditer(r">>>PROGRESS>>>(\d+)/(\d+)<<<", data):
            cur, total = int(m.group(1)), int(m.group(2))
            self.progress.setRange(0, total)
            self.progress.setValue(cur)
            self._prog_shot = "%s %d / %d" % (unit, cur, total)
            self.progress.setFormat(self._prog_shot)
        # Maya : exports lances apres la mise a jour des rigs
        for m in re.finditer(r">>>EXPORTPROGRESS>>>(\d+)/(\d+)<<<", data):
            cur, total = int(m.group(1)), int(m.group(2))
            self.progress.setRange(0, total)
            self.progress.setValue(cur)
            self._prog_shot = "export %d / %d" % (cur, total)
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
            if (
                MAYA_RESULT_START in s
            ):  # verdict json (une ligne) : lu a la fin, pas affiche
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
        if mode == "maya_apply":
            self._on_maya_finished(code, took)
            return
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
            return newp
        return None

    # ------------------------------------------------------ fin d'un run Maya
    def _maya_result(self):
        """Verdict json du moteur Maya, ou None si le process est mort sans le donner."""
        a = self._buf.rfind(MAYA_RESULT_START)
        if a == -1:
            return None
        b = self._buf.find(MAYA_RESULT_END, a)
        if b == -1:
            return None
        try:
            res = json.loads(self._buf[a + len(MAYA_RESULT_START) : b])
        except Exception:
            return None
        return res if isinstance(res, dict) else None

    @staticmethod
    def _maya_summary(res, code, took):
        """(ok, message) lisible d'un run Maya. Le VERDICT du moteur fait foi, pas le code
        de sortie ; sans verdict, le process est mort en route (crash Maya)."""
        if res is None:
            return False, (
                "✗ Maya stopped before the end (exit %s, %s) — treat this scene as NOT "
                "updated; see the log." % (code, took)
            )
        verdict = res.get("verdict")
        rigs = res.get("rigs") or []
        exports = res.get("exports") or []
        saved = res.get("saved")
        if saved:
            saved_txt = "scene saved as %s" % os.path.basename(saved)
        else:
            saved_txt = "scene not saved" if rigs else "scene unchanged"
        exp_ok = [
            "%s %s" % (e.get("product") or e.get("name"), e.get("to"))
            for e in exports
            if e.get("ok")
        ]
        exp_ko = [e.get("name") or e.get("uuid") for e in exports if not e.get("ok")]
        if verdict == "refused_lost_anim":
            # QUEL rig perd de l'anim : l'artiste peut le decocher et relancer le reste
            losers = [
                "%s (%d)" % (rig_label(r.get("id")), r["lost"])
                for r in rigs
                if (r.get("lost") or 0) > 0
            ]
            return False, (
                "✗ Refused: the new rig(s) lose %d animation edit(s)%s. Nothing was saved "
                "or exported — untick %s and retry, or check it in Maya."
                % (
                    res.get("lost") or 0,
                    (" — " + ", ".join(losers)) if losers else "",
                    "those rigs" if len(losers) > 1 else "that rig",
                )
            )
        if verdict == "refused_swap_errors":
            return False, (
                "✗ Refused: some references could not be swapped (see the log). "
                "Nothing was saved or exported."
            )
        if verdict == "save_failed":
            return False, (
                "✗ The new scene version could not be saved (Prism). "
                "Nothing was exported."
            )
        if verdict == "nothing_to_do":
            return True, (
                "Nothing to do: none of the ticked rigs is outdated and no export was "
                "ticked."
            )
        if verdict == "dry_run":
            return True, (
                "✓ Dry run OK in %s: %d rig(s) swapped without losing animation. Nothing "
                "was written." % (took, len(rigs))
            )
        if verdict in ("ok", "export_failed"):
            parts = [
                "%d rig(s) updated" % len(rigs) if rigs else "rigs unchanged",
                saved_txt,
            ]
            if exp_ok:
                parts.append("exported: " + ", ".join(exp_ok))
            if exp_ko:
                parts.append("FAILED export(s): " + ", ".join(exp_ko))
            # un export rate a pu laisser un dossier vNNN casse, qui passe pour le dernier
            broken = [
                "/".join(e["broken_version"].rstrip("/").split("/")[-2:])
                for e in exports
                if e.get("broken_version")
            ]
            if broken:
                parts.append(
                    "BROKEN version left on disk, delete it: " + ", ".join(broken)
                )
            if res.get("warnings"):  # ex. scene ouverte avec des references manquantes
                parts.append("%d warning(s), see the log" % len(res["warnings"]))
            ok = verdict == "ok"
            return ok, "%s %s (%s)." % ("✓" if ok else "⚠", " · ".join(parts), took)
        errors = "; ".join(res.get("errors") or []) or verdict or "?"
        return False, "✗ Update failed (%s): %s" % (took, errors)

    def _on_maya_finished(self, code, took):
        res = self._maya_result()
        run_scene, self._run_scene = self._run_scene, ""
        # version-up -> le champ suit la nouvelle version
        newp = self._pick_saved_scene()
        ok, msg = self._maya_summary(res, code, took)
        for w in (res or {}).get("warnings") or []:
            self.log.appendPlainText("[UI] warning: %s" % w)
        for e in (res or {}).get("exports") or []:
            self.log.appendPlainText(
                "[UI] export %-24s %s  %s"
                % (
                    e.get("name") or e.get("uuid"),
                    "OK " if e.get("ok") else "KO ",
                    ("%s -> %s" % (e.get("from") or "-", e.get("to")))
                    if e.get("ok")
                    else (e.get("error") or ""),
                )
            )
            # sanity check studio joue en batch : ce qui a echoue, meme accepte (warnings)
            for c in e.get("sanity") or []:
                self.log.appendPlainText(
                    "[UI]     sanity check %s: %s" % (c.get("severity"), c.get("label"))
                )
        self.log.appendPlainText(
            "[UI] ===== MAYA UPDATE %s (exit %s, %s) ====="
            % ("FINISHED" if ok else "FAILED", code, took)
        )
        self.log.appendPlainText("[UI] " + msg)
        # la table reflete la scene sur disque : la nouvelle version, ou la meme
        cur = self.ed_hip.text().strip()
        if newp or os.path.normcase(cur) == os.path.normcase(run_scene):
            self._read_maya_scene(preserve=not newp, force=True)
        self.status.showMessage(msg)

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

    def _layer_cell(self, d, ld):
        """(texte, tooltip) de la colonne des layers suivis.

        1 layer  -> 'v012 -> v014' (inchange).
        N layers -> 'k/n stale', et le detail par layer va dans le tooltip : la colonne
        reste courte, l'info reste accessible."""
        c = self._combined(d)
        tips = []
        for name, e in c["present"]:
            tips.append(
                "%s : %s%s"
                % (
                    self._pretty_layer(name),
                    self._pair(e.get("consumed"), e.get("latest")),
                    "   OUTDATED"
                    if e.get("stale")
                    else (
                        "   PINNED %s in the USD Layer Stack" % e["pinned"]
                        if e.get("pinned")
                        else ""
                    ),
                )
            )
        for name in c["ignored"]:
            tips.append(
                "%s : not consumed by this shot -> ignored" % self._pretty_layer(name)
            )
        tip = "\n".join(tips)
        if len(c["present"]) <= 1:
            consumed = ld.get("consumed") or d.get("consumed_version")
            latest = ld.get("latest") or d.get("latest_version")
            if ld.get("pinned"):
                # 'v018 (pinned, latest v020)' : le retard se voit, mais il est voulu
                return (
                    "%s (pinned%s)"
                    % (
                        consumed or ld["pinned"],
                        (", latest %s" % latest)
                        if ld.get("pinned_behind") and latest
                        else "",
                    ),
                    tip,
                )
            return self._pair(consumed, latest), tip
        n_stale = sum(1 for _, e in c["present"] if e.get("stale"))
        return "%d/%d stale" % (n_stale, len(c["present"])), tip

    def _caches_for(self, d):
        """[{path, name, product}] des lop_filecache du shot. Retombe sur l'ancien
        `cache_node` seul pour un snapshot ecrit par une version anterieure."""
        caches = d.get("caches")
        if caches:
            return caches
        one = d.get("cache_node")
        return [{"path": one, "name": one.split("/")[-1], "product": ""}] if one else []

    def _cache_summary(self, d):
        """Cellule 'Caches' : 'coches/total ▸', comme les colonnes SOP et Renders.
        Cliquable pour choisir QUELS caches executer."""
        caches = self._caches_for(d)
        if not caches:
            return ""
        sel = self._cache_sel_for(d)
        n = sum(1 for c in caches if c.get("path") in sel)
        return "%d/%d  ▸" % (n, len(caches))

    def _update_ignored_note(self, data):
        """Message DISCRET (gris, a cote du bouton) : quels layers suivis ont ete
        ignores, et sur combien de shots. Vide s'il n'y a rien a signaler."""
        counts = {}
        for d in data or []:
            for name in self._combined(d)["ignored"]:
                counts[name] = counts.get(name, 0) + 1
        if not counts:
            self.lbl_ignored.setText("")
            self.lbl_ignored.setToolTip("")
            return
        parts = [
            "%s (%d shot%s)" % (self._pretty_layer(n), k, "s" if k > 1 else "")
            for n, k in sorted(counts.items(), key=lambda x: -x[1])
        ]
        self.lbl_ignored.setText("· ignored: " + ", ".join(parts))
        self.lbl_ignored.setToolTip(
            "These tracked layers aren't consumed by those shots, so they can't say "
            "anything about staleness there.\nThose shots are judged on the remaining "
            "tracked layers (both in ANY and ALL mode)."
        )

    def _pair(self, a, b):
        if not a and not b:
            return ""
        if a == b:
            return a or b or ""
        return "%s -> %s" % (a or "?", b or "?")

    def _combined(self, d):
        """Verdict multi-layers de ce shot. MEME fonction que le moteur
        (preview.combine_layers) -> l'UI ne peut pas afficher autre chose que ce qui
        sera applique."""
        return preview.combine_layers(
            d.get("layers") or {}, self._tracked(), self._layer_mode()
        )

    def _layer_entry(self, d):
        """Donnees du layer DECISIF pour ce shot (celui qui explique le verdict)."""
        c = self._combined(d)
        if not c["present"]:
            return None
        for name, e in c["present"]:
            if name == c["deciding"]:
                return e
        return c["present"][0][1]

    def _row_state(self, d):
        """State of a row for the selected layers, computed client-side."""
        if not d.get("import_node"):
            return "no_import"
        if d.get("state") == "error":
            return "error"
        layers = d.get("layers")
        if not layers:  # old payload without per-layer data
            return d.get("state", "error")
        if d.get("state") == "no_record":
            # le moteur n'a PAS pu conclure (aucun releve) : ne pas repeindre en vert
            return "no_record"
        c = self._combined(d)
        if not c["present"] or c["stale"] is None:
            return "no_layer"
        if c["stale"]:
            return "outdated"
        return "pinned" if c["pinned"] else "uptodate"

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

                layer_txt, layer_tip = self._layer_cell(d, ld)
                vals = [
                    layer_txt,
                    STATE_TEXT.get(state, state),
                    self._sop_summary(d),
                    self._render_summary(d),
                    self._cache_summary(d),
                ]
                for c, v in enumerate(vals, start=1):
                    cell = QtWidgets.QTableWidgetItem(str(v))
                    if c == 1 and layer_tip:  # detail par layer + ce qui est ignore
                        cell.setToolTip(layer_tip)
                    if c == 2 and state == "pinned":
                        cell.setToolTip(
                            "Pinned in the USD Layer Stack (%s): a newer version exists, "
                            "but the pin is the artist's choice.\nThe tool never "
                            "unpins: a re-cache keeps the pinned version. Unpin it in "
                            "Houdini to move to the latest." % pins_text(d.get("pins"))
                        )
                        cell.setForeground(QtGui.QColor(col["sop"]))
                    if c == 5 and self._caches_for(d):  # Caches cell -> clickable
                        sel = self._cache_sel_for(d)
                        cell.setToolTip(
                            "Click to choose which USD caches to re-cache.\n"
                            + "\n".join(
                                "%s %s   [%s]"
                                % (
                                    "x" if c2.get("path") in sel else " ",
                                    c2.get("product") or "?",
                                    c2.get("name") or "",
                                )
                                for c2 in self._caches_for(d)
                            )
                        )
                        cell.setForeground(QtGui.QColor(col["sop"]))
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
        self._update_ignored_note(data)
        self._update_farm_button()
        self._update_apply_count()

    # --------------------------------------------- reglages ferme des renders
    def _update_farm_button(self):
        """Bouton 'Farm' : visible pour une scene Houdini qui a des LOP_Render ; dit si
        les renders partent avec les reglages de la scene ou avec des overrides."""
        show = (not self._is_maya()) and has_renders(self._data)
        self.lbl_farm.setVisible(show)
        self.b_farm.setVisible(show)
        if not show:
            return
        txt = farm_overrides_text(self._farm_overrides)
        self.b_farm.setText(
            ("%d override(s)  ▸" % len(self._farm_overrides))
            if txt
            else "scene settings  ▸"
        )
        self.b_farm.setToolTip(
            "Farm settings of the renders submitted by this update:\n"
            + (txt if txt else "each render keeps its own settings from the scene")
            + "\n(click to change: frames, priority, frames per task, pool, group...)"
        )

    def _open_farm_dialog(self):
        dlg = FarmSettingsDialog(self, farm_values(self._data), self._farm_overrides)
        ok = dlg.exec() if hasattr(dlg, "exec") else dlg.exec_()
        if not ok:
            return
        self._farm_overrides = dlg.overrides()
        self._farm_for = self._scene_key()
        self._update_farm_button()

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
        return scene_family(self.ed_hip.text().strip())

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
        "cache_unselected": {},  # caches DECOCHES par shot (cf _cache_sel_for)
        "render_layers": {},  # layers a rendre par shot (override ; defaut = Enabled node)
        # releve par shot de ce que le dernier cache a consomme/publie -> SOURCE DE
        # VERITE de la peremption, agnostique au type de node d'import
        "cached": {},
        "tracked_layer": "",  # forme historique (relue, tenue a jour)
        "tracked_layers": [],  # layers suivis pour CETTE scene
        "tracked_mode": "or",  # or = un seul suffit | and = tous
        # scene Maya : uuids des states d'export a lancer (None = ceux coches dans la
        # scene). Stocke le CHOIX, pas un defaut : un state ajoute plus tard reste decoche
        "export_states": None,
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
        # on ecrit LES DEUX formes : une version plus ancienne de l'outil
        # ouvrant le meme json partage retombe sur ses pieds.
        # (scene Maya : pas de layers suivis, on n'ecrit pas un reglage qui n'existe pas)
        if not self._is_maya():
            sel = self._tracked()
            self._fx_store["tracked_layers"] = sel
            self._fx_store["tracked_layer"] = sel[0]
            self._fx_store["tracked_mode"] = self._layer_mode()
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
            "maya": ("read from the .ma (no Maya)", "green"),
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

    def _newer_scene_text(self, cur_v, latest):
        """Texte du garde-fou, SELON le mode de sauvegarde. Le risque n'est pas le meme :
        - Version-up : on publie vLATEST+1 depuis vCUR -> le travail v(CUR+1)..vLATEST
          disparait de la nouvelle version ;
        - Leave untouched : AUCUNE version n'est creee (le message disait "publish v176",
          faux), mais les caches sont construits depuis le setup de vCUR -> ce qui a
          change dans v(CUR+1)..vLATEST n'y sera pas."""
        head = "A newer version of this scene exists: <b>v%03d</b>.<br><br>" % latest
        span = (
            ("v%03d" % latest)
            if cur_v + 1 == latest
            else ("v%03d…v%03d" % (cur_v + 1, latest))
        )
        if (
            self._is_maya()
        ):  # meme risque, mais ce qui part en aval, ce sont les EXPORTS
            if self._save_mode() == SAVE_LEAVE:
                return head + (
                    "The scene won't be saved, but the exports will be made from "
                    "<b>v%03d</b>: whatever was animated in %s <b>won't be in them</b>."
                    % (cur_v, span)
                )
            return head + (
                "You are about to update the rigs of <b>v%03d</b> and publish v%03d — "
                "everything animated in %s would be <b>ignored</b>."
                % (cur_v, latest + 1, span)
            )
        if self._save_mode() == SAVE_LEAVE:
            return head + (
                "The scene won't be saved, but the caches will be built from "
                "<b>v%03d</b>: whatever changed in %s (cache setup, FX, lights…) "
                "<b>won't be in them</b>." % (cur_v, span)
            )
        return head + (
            "You are about to update from <b>v%03d</b> and publish v%03d — everything "
            "saved in %s would be <b>ignored</b>." % (cur_v, latest + 1, span)
        )

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
        box.setText(self._newer_scene_text(cur_v, latest))
        box.setInformativeText("What do you want to do?")
        # /!\ enum SCOPE (ButtonRole.X), jamais `box.AcceptRole` : PySide6 6.5 (hython)
        # tolere le nom court sur une instance, 6.11 (l'UI, via uv) leve AttributeError.
        # Les tests tournaient sous hython -> le crash n'apparaissait qu'en vrai.
        role = QtWidgets.QMessageBox.ButtonRole
        b_latest = box.addButton("Use latest (v%03d)" % latest, role.AcceptRole)
        b_anyway = box.addButton("Continue anyway", role.DestructiveRole)
        b_cancel = box.addButton("Cancel", role.RejectRole)
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
            QtWidgets.QMessageBox.warning(self, "Scene", "No scene found:\n%s" % hip)
            return
        if (
            self._is_maya()
        ):  # re-lecture du .ma + des versions publiees, selection gardee
            self._read_maya_scene(preserve=True, force=True)
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

    def _cache_sel_for(self, d):
        """Set des CHEMINS de caches coches pour ce shot. Source = json partage, ou on
        stocke les DECOCHES (`cache_unselected`) : un cache ajoute plus tard au setup est
        donc coche par defaut, comme pour la chaine SOP. Defaut = tout coche."""
        self._ensure_store()
        shot = d.get("shot", "")
        all_paths = [c.get("path") for c in self._caches_for(d)]
        if shot not in self._cache_selection:
            off = set(self._fx_store.get("cache_unselected", {}).get(shot, []))
            self._cache_selection[shot] = [p for p in all_paths if p not in off]
        return set(self._cache_selection[shot])

    def _save_cache_sel(self, shot, checked_paths, all_paths, flush=True):
        self._ensure_store()
        checked = set(checked_paths)
        self._cache_selection[shot] = [p for p in all_paths if p in checked]
        self._fx_store.setdefault("cache_unselected", {})[shot] = [
            p for p in all_paths if p not in checked
        ]
        if flush:
            self._save_hip_store()

    def _on_cell_clicked(self, row, col):
        if self._is_maya() or col not in (3, 4, 5):
            return
        ident = self.table.item(row, 0).data(Qt.UserRole)
        d = next((x for x in self._data if x.get("id") == ident), None)
        if not d:
            return
        if col == 3 and d.get("fx_chain"):
            self._open_fx_dialog(d)
        elif col == 4 and self._render_layers_for(d):
            self._open_render_dialog(d)
        elif col == 5 and self._caches_for(d):
            self._open_cache_dialog(d)

    def _open_cache_dialog(self, d):
        shot = d.get("shot", "")
        caches = self._caches_for(d)
        dlg = CachePickerDialog(self, shot, caches, self._cache_sel_for(d))
        ok = dlg.exec() if hasattr(dlg, "exec") else dlg.exec_()
        if not ok:
            return
        all_paths = [c.get("path") for c in caches]
        self._save_cache_sel(shot, dlg.checked_paths(), all_paths)
        if dlg.apply_to_all():
            keep_products = {
                c.get("product")
                for c in caches
                if c.get("path") in set(dlg.checked_paths())
            }
            self._apply_cache_sel_to_all(keep_products)
        self._populate(self._data, preserve=True)  # refresh the summary cell

    def _apply_cache_sel_to_all(self, keep_products):
        """Propage la selection a TOUS les shots, PAR PRODUIT : les chemins de node
        different d'un shot a l'autre, les produits publies non."""
        for d in self._data:
            caches = self._caches_for(d)
            if not caches:
                continue
            all_paths = [c.get("path") for c in caches]
            keep = [c["path"] for c in caches if c.get("product") in keep_products]
            self._save_cache_sel(d.get("shot", ""), keep, all_paths, flush=False)
        self._save_hip_store()

    def _build_cache_plan(self, ids):
        """{item_id: [chemins de caches a executer]} pour les items COCHES.

        /!\\ On ecrit TOUJOURS une entree pour un item coche qui a des caches, meme si la
        liste est vide : cote moteur, entree absente = "tous", liste vide = "aucun".
        Sans ca, tout decocher recacherait tout."""
        plan = {}
        idset = set(ids)
        for d in self._data:
            if d.get("id") not in idset:
                continue
            caches = self._caches_for(d)
            if not caches:
                continue
            sel = self._cache_sel_for(d)
            plan[d["id"]] = [c["path"] for c in caches if c.get("path") in sel]
        return plan

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
            # startswith : un rig Maya peut etre "OUTDATED · file missing"
            outdated = self.table.item(r, 2).text().startswith("OUTDATED")
            self.table.item(r, 0).setCheckState(
                Qt.Checked if outdated else Qt.Unchecked
            )
        self._update_apply_count()

    def _update_apply_count(self, *_args):
        """Show how many shots are ticked, right on the action button."""
        if self._populating:
            return
        n = len(self._selected()[0])
        label = APPLY_LABEL_MAYA if self._is_maya() else APPLY_LABEL
        self.b_apply.setText("%s (%d)" % (label, n) if n else label)

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
        if self._is_maya():  # rien a charger dans Maya pour LIRE une scene .ma
            self._read_maya_scene(force=True)
            return
        self._start("status", ["--status"])

    def _maya_update_summary(self, ids):
        """Texte de confirmation d'un update Maya : ce qui va arriver aux rigs, a la scene
        et aux exports -- dit AVANT, pas decouvert apres."""
        idset = set(ids)
        rigs = [r for r in self._maya_rigs if r.get("id") in idset]
        stale = [r for r in rigs if r.get("stale")]
        lines = []
        for r in rigs:
            lines.append(
                "  • %s   %s%s"
                % (
                    rig_label(r.get("id")),
                    self._pair(r.get("version"), r.get("latest")),
                    "" if r.get("stale") else "   (up to date: nothing to swap)",
                )
            )
        sel = set(self._export_sel())
        exports = [e for e in self._maya_exports if e["uuid"] in sel]
        exp_txt = (
            ", ".join("%s (%s)" % (e["name"], e["product"] or "?") for e in exports)
            if exports
            else "none"
        )
        if not stale:
            scene_txt = "Scene: unchanged (no outdated rig ticked), not saved."
        elif self._save_mode() == SAVE_VERSION_UP:
            scene_txt = "Scene: a NEW version will be saved (version-up)."
        elif exports:
            scene_txt = (
                "Scene: LEFT UNTOUCHED - the .ma is not written. The exports get the "
                "comment '(scene not saved)': their source scene won't contain this update."
            )
        else:
            scene_txt = (
                "Scene: LEFT UNTOUCHED and no export: DRY RUN, nothing is written."
            )
        return "\n".join(
            lines
            + [
                "",
                scene_txt,
                "Exports after the update: %s." % exp_txt,
                "",
                "Safety: if the new rigs lose animation (failed reference edits), the "
                "update is refused - nothing is saved or exported.",
                "Maya runs in the background (loading the scene takes a while).",
            ]
        )

    def _recache_maya(self, ids):
        """Update d'une scene Maya : rigs coches -> verif -> sauvegarde -> exports."""
        idset = set(ids)
        stale = [r for r in self._maya_rigs if r.get("id") in idset and r.get("stale")]
        uuids = self._export_sel()
        if not stale and not uuids:
            QtWidgets.QMessageBox.information(
                self,
                "Nothing to do",
                "None of the ticked rigs is outdated, and no export is ticked.",
            )
            return
        if not self._guard_newer_scene():
            return
        msg = "Update %d rig(s) in %s?\n\n%s" % (
            len(stale),
            os.path.basename(self.ed_hip.text().strip()),
            self._maya_update_summary(ids),
        )
        yes = QtWidgets.QMessageBox.StandardButton.Yes
        if QtWidgets.QMessageBox.question(self, "Confirm update", msg) != yes:
            return
        extra = ["--apply", "--rigs"] + [r["id"] for r in stale]
        if uuids:
            extra += ["--export"] + uuids
        if self._save_mode() == SAVE_LEAVE:
            extra.append("--no-save")
        extra += ["--comment", MAYA_COMMENT]
        self._start_maya(extra)

    def recache_selected(self):
        ids, labels = self._selected()
        if not ids:
            QtWidgets.QMessageBox.information(
                self,
                "Selection",
                "No rig ticked." if self._is_maya() else "No shot ticked.",
            )
            return
        if self._is_maya():
            self._recache_maya(ids)
            return
        # garde-fou AVANT tout : ne pas updater depuis une scene perimee (sinon le
        # version-up ecraserait le travail fait entre-temps)
        if not self._guard_newer_scene():
            return
        # FX: quels caches SOP re-simuler par shot (coches dans l'UI) -> plan json
        plan = self._build_fx_plan(ids)
        n_sop = sum(len(v) for v in plan.values())
        # quels lop_filecache executer par item (coches dans l'UI) -> plan json
        cplan = self._build_cache_plan(ids)
        n_cache_off = sum(1 for v in cplan.values() if not v)
        # Lighting: quels shots re-rendre a la ferme + leurs layers -> plan json
        rplan = self._build_render_plan(ids)
        n_render_shots = len(rplan)
        n_jobs = sum(len(v) for v in rplan.values())
        extra_msg = ""
        idset = set(ids)
        pinned = [
            "%s (%s)" % (d.get("shot", "?"), pins_text(d.get("pins")))
            for d in self._data
            if d.get("id") in idset and d.get("pins")
        ]
        if pinned:
            # le pin est un choix de l'artiste : l'outil ne le retire pas -> on DIT que
            # le cache gardera ces versions, pour ne pas croire a une mise a jour
            extra_msg += (
                "\n(PINNED layers kept: %s. The re-cache uses the pinned versions; "
                "unpin them in Houdini to move to the latest.)"
                % ", ".join(pinned[:4])
                + (" ..." if len(pinned) > 4 else "")
            )
        if n_cache_off:
            extra_msg += (
                "\n(%d shot(s) with NO cache ticked: the import is bumped and the "
                "render submitted, but nothing is re-cached.)" % n_cache_off
            )
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
            farm_txt = farm_overrides_text(self._farm_overrides)
            extra_msg += "\nFarm: %s." % (
                farm_txt or "each render keeps its own settings from the scene"
            )
            if not os.environ.get("PRISM_LAUNCH_ENV"):
                # un submit GUI copie dans les jobs l'env du profil du launcher Prism
                # (OCIO...) : il n'arrive ici que si l'outil vient du shelf Houdini
                extra_msg += (
                    "\n⚠ Tool not launched from Houdini: the farm jobs won't get the "
                    "environment of your Prism launcher profile (OCIO...). Prefer the "
                    "Houdini shelf button."
                )
        msg = "Update %d shot(s)?\n\n%s\n\n%s%s" % (
            len(ids),
            ", ".join(labels),
            self._save_mode_summary(ids, bool(rplan)),
            extra_msg,
        )
        yes = QtWidgets.QMessageBox.StandardButton.Yes
        if QtWidgets.QMessageBox.question(self, "Confirm update", msg) != yes:
            return
        # cocher = intention explicite -> on cache TOUS les shots coches, meme ceux
        # deja a jour (--force ; sinon le moteur skippe les non-perimes).
        extra = ["--apply", "--force", "--shots"] + ids
        if self._save_mode() == SAVE_LEAVE:
            extra.append("--no-save")  # scene intacte : aucune version dans la chaine
        if plan:
            pf = os.path.join(tempfile.gettempdir(), "lop_update_cache_fx_plan.json")
            try:
                with open(pf, "w", encoding="utf-8") as fh:
                    json.dump(plan, fh)
                extra += ["--fx-plan", pf]
            except Exception as ex:
                self.log.appendPlainText("\n[UI] fx-plan write failed: %s" % ex)
        if cplan:
            cf = os.path.join(tempfile.gettempdir(), "lop_update_cache_cache_plan.json")
            try:
                with open(cf, "w", encoding="utf-8") as fh:
                    json.dump(cplan, fh)
                extra += ["--cache-plan", cf]
            except Exception as ex:
                self.log.appendPlainText("\n[UI] cache-plan write failed: %s" % ex)
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
        if rplan and self._farm_overrides:
            ff = os.path.join(tempfile.gettempdir(), "lop_update_cache_farm_plan.json")
            try:
                with open(ff, "w", encoding="utf-8") as fh:
                    json.dump({"*": self._farm_overrides}, fh)
                extra += ["--farm-plan", ff]
            except Exception as ex:
                # pas de reglages demandes = on ne soumet PAS avec ceux de la scene
                # en silence : on s'arrete
                QtWidgets.QMessageBox.warning(
                    self, "Farm settings", "Couldn't write the farm settings:\n%s" % ex
                )
                return
        self._start("apply", extra)


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = Main()
    w.show()
    sys.exit(app.exec() if hasattr(app, "exec") else app.exec_())


if __name__ == "__main__":
    main()
