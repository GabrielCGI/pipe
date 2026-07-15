"""
Channels Cleaner — supprime proprement des layers/channels persistants d'un script Nuke.

Limitation Nuke : un layer cree via nuke.Layer() (ou add_layer dans le .nk) reste
enregistre globalement dans la session et ne peut pas etre supprime en global, seulement
par branche. Le contournement consiste a reecrire le .nk en retirant les lignes add_layer
des layers choisis, puis a rouvrir le script nettoye.

Ce module produit un nouveau script CONFORME au pipeline Prism (nommage, emplacement global,
version +1, versioninfo.json) en s'appuyant sur l'API Prism (pcore) chargee dans Nuke. Si le
script courant n'est pas un scenefile Prism valide, on retombe sur un nommage simple (_clean.nk
ou increment du nombre final).

Usage : appele via le bouton « Clean Channels… » du node DMP_EXR_Layers, ou directement :
    import export_layers.channels_cleaner as cc
    cc.run_cleaner()
"""

import os
import re

import nuke

# PySide2 (Nuke < 16) ou PySide6 (Nuke >= 16)
if nuke.NUKE_VERSION_MAJOR >= 16:
    from PySide6 import QtWidgets
else:
    from PySide2 import QtWidgets


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Layers Nuke par defaut (jamais proposes au nettoyage)
DEFAULT_LAYERS = [
    "rgb",
    "rgba",
    "alpha",
    "depth",
    "motion",
    "forward",
    "backward",
    "disparity",
    "disparityL",
    "disparityR",
    "mask",
    "rotopaint_mask",
    "mask_planartrack",
    "mask_splinewarp",
    "deep",
]

# Pattern d'un layer DMP : prefixe _###_ (ex. _100_BG)
DMP_LAYER_RE = re.compile(r"^_\d{3}_")

# Suffixe des passes de rendu importees (Read EXR), ex. _040_COMP_main_RGBA.
# Elles matchent le pattern _###_ mais ne sont pas creees par l'outil DMP : on ne
# les pre-coche pas (elles restent visibles et cochables manuellement).
RENDER_LAYER_SUFFIX = "_main_RGBA"

# Nom des Group nodes crees par l'outil export_layers
DMP_GROUP_PREFIX = "DMP_EXR_Layers"


# ---------------------------------------------------------------------------
# Layer discovery
# ---------------------------------------------------------------------------


def _get_user_layers():
    """Return all layers in the script minus the default Nuke layers."""
    layers = list(nuke.layers())
    return [layer for layer in layers if layer not in DEFAULT_LAYERS]


def _get_active_dmp_layers():
    """Collect the layer names registered by all active DMP_EXR_Layers group nodes.

    Source of truth = the `channels` knob of each internal AddChannels node (created
    by export_layers._rebuild_internals as `AC_<layername>` with channels set to the
    exact layer name passed to nuke.Layer()). Reading these guarantees an exact match
    with nuke.layers(), unlike reconstructing names from the prefix/name knobs.

    These are the layers currently "in use" — they must NOT be flagged obsolete.
    """
    active = set()
    # Forcer le scan depuis la racine : un PyScript knob sur un Group s'execute
    # dans le contexte interieur du groupe, ou nuke.allNodes("Group") renvoie [].
    for node in nuke.allNodes("Group", nuke.root(), recurseGroups=True):
        if not node.name().startswith(DMP_GROUP_PREFIX):
            continue
        with node:  # enter the group context
            for ac in nuke.allNodes("AddChannels"):
                layer = ac["channels"].value()
                if not layer:
                    nm = ac.name()
                    if nm.startswith("AC_"):
                        layer = nm[3:]  # AC__100_GROUND_MG -> _100_GROUND_MG
                if layer:
                    active.add(layer)
    return active


def _get_obsolete_dmp_layers(user_layers, active):
    """Return DMP-pattern layers (_###_) to pre-check for deletion.

    A layer is considered obsolete (pre-checked) when it matches the DMP prefix,
    is not referenced by any active DMP node, and is not an imported render pass
    (suffix RENDER_LAYER_SUFFIX) — those are left unchecked but still listed.
    """
    return [
        layer
        for layer in user_layers
        if DMP_LAYER_RE.match(layer)
        and layer not in active
        and not layer.endswith(RENDER_LAYER_SUFFIX)
    ]


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------


class ChannelsCleanerDialog(QtWidgets.QDialog):
    """Checkbox grid to pick which layers to strip from the script."""

    def __init__(self, layers, precheck=None, parent=None):
        super(ChannelsCleanerDialog, self).__init__(parent)
        self.setWindowTitle("Channels Cleaner")
        self.checkboxes = []
        precheck = set(precheck or [])

        main_layout = QtWidgets.QVBoxLayout(self)

        info = QtWidgets.QLabel(
            "Cochez les layers a supprimer. Les layers DMP obsoletes "
            "(non utilises par un node DMP) sont pre-coches."
        )
        info.setWordWrap(True)
        main_layout.addWidget(info)

        # Nombre de colonnes selon le nombre de layers
        count = len(layers)
        if count <= 15:
            num_cols = 1
        elif count <= 30:
            num_cols = 2
        elif count <= 60:
            num_cols = 3
        else:
            num_cols = 4

        num_rows = (count + num_cols - 1) // num_cols

        # Grille de checkboxes (remplissage colonne par colonne)
        grid = QtWidgets.QGridLayout()
        for i, layer in enumerate(layers):
            row = i % num_rows
            col = i // num_rows
            cb = QtWidgets.QCheckBox(layer)
            if layer in precheck:
                cb.setChecked(True)
                # Mise en evidence visuelle des layers DMP obsoletes
                font = cb.font()
                font.setBold(True)
                cb.setFont(font)
                cb.setStyleSheet("color: #d08770;")
            self.checkboxes.append(cb)
            grid.addWidget(cb, row, col)
        main_layout.addLayout(grid)

        # Boutons Select All / Deselect All
        btn_layout = QtWidgets.QHBoxLayout()
        select_all_btn = QtWidgets.QPushButton("Select All")
        deselect_all_btn = QtWidgets.QPushButton("Deselect All")
        select_all_btn.clicked.connect(lambda: self._set_all(True))
        deselect_all_btn.clicked.connect(lambda: self._set_all(False))
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # OK / Cancel
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _set_all(self, checked):
        for cb in self.checkboxes:
            cb.setChecked(checked)

    def selected_layers(self):
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]


# ---------------------------------------------------------------------------
# Script rewriting
# ---------------------------------------------------------------------------


def _write_cleaned(src_path, dst_path, layers_del):
    """Copy src_path → dst_path, dropping add_layer lines for the selected layers."""
    dst_dir = os.path.dirname(dst_path)
    if dst_dir and not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    with open(src_path) as oldfile, open(dst_path, "w") as newfile:
        for line in oldfile:
            if "add_layer" in line and any(layer in line for layer in layers_del):
                continue
            newfile.write(line)


def jp_nuke_new(nuke_old):
    """Fallback naming (non-Prism): increment trailing number or append _clean.

    'comp_001.nk' → 'comp_002.nk' ; 'comp.nk' → 'comp_clean.nk'
    """
    x = nuke_old.replace(" ", "")[:-3]
    trailing = re.sub(r".*?([0-9]*)$", r"\1", x)
    if len(trailing) != 0:
        y = str(int(trailing) + 1)
        x = x.replace(" ", "")[: -len(y)]
        return x + y + ".nk"
    return x + "_clean.nk"


# ---------------------------------------------------------------------------
# Prism helpers
# ---------------------------------------------------------------------------


def _get_pcore():
    """Return the running Prism core exposed globally in Nuke, or None."""
    import __main__

    return getattr(__main__, "pcore", None)


def _prism_scenefile_data(pcore, path):
    """Return Prism entity data for path if it is a valid scenefile, else None."""
    try:
        data = pcore.getScenefileData(path, getEntityFromPath=True)
    except Exception:
        return None
    if data and "department" in data:
        return data
    return None


def _prism_next_version_path(pcore, fname_data):
    """Build the next-version scene path (global) via Prism, or '' on failure."""
    try:
        return pcore.generateScenePath(
            entity=fname_data,
            department=fname_data["department"],
            task=fname_data.get("task", ""),
            extension=".nk",
            version="",  # Prism resolves to highest + 1
            location="global",
        )
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_cleaner():
    """Show the cleaner dialog and write a cleaned, pipeline-conformant script."""
    old = nuke.scriptName()
    if not old:
        nuke.message("Sauvegardez d'abord le script avant de nettoyer les channels.")
        return

    if nuke.modified():
        if not nuke.ask(
            "Le script courant a des modifications non sauvegardees.\n"
            "Le nettoyage repart de la DERNIERE version sauvegardee sur disque.\n\n"
            "Continuer ?"
        ):
            return

    user_layers = _get_user_layers()
    if not user_layers:
        nuke.message("Aucun layer utilisateur. Rien a nettoyer :)")
        return

    active = _get_active_dmp_layers()
    if not active:
        if not nuke.ask(
            "Aucun node DMP_EXR_Layers trouve dans le script courant.\n"
            "Tous les layers _###_ seront proposes a la suppression.\n\n"
            "Continuer ?"
        ):
            return
    obsolete = _get_obsolete_dmp_layers(user_layers, active)

    dialog = ChannelsCleanerDialog(user_layers, precheck=obsolete)
    if not dialog.exec_():
        return

    layers_del = dialog.selected_layers()
    if not layers_del:
        nuke.message("Rien de selectionne, rien a faire :)")
        return

    # Determine the destination path (Prism-conformant if possible).
    pcore = _get_pcore()
    new_path = ""
    write_info = False
    fname_data = None

    if pcore is not None:
        fname_data = _prism_scenefile_data(pcore, old)
        if fname_data is not None:
            new_path = _prism_next_version_path(pcore, fname_data)
            write_info = bool(new_path)

    if not new_path:
        # Fallback hors pipeline Prism.
        new_path = jp_nuke_new(old)

    if os.path.exists(new_path):
        nuke.message("Le fichier cible existe deja :\n{}".format(new_path))
        return

    _write_cleaned(old, new_path, layers_del)

    if write_info:
        try:
            pcore.saveSceneInfo(new_path, details=fname_data)
        except Exception as exc:
            nuke.message(
                "Script nettoye ecrit mais versioninfo.json non genere :\n{}".format(
                    exc
                )
            )

    nuke.scriptClose()
    nuke.scriptOpen(new_path)
