import qtpy.QtWidgets as qt
import maya.cmds as cmds


ANIM_CURVE_TYPES = ("animCurveTA", "animCurveTL", "animCurveTU", "animCurveTT")


class TransferAnimation(qt.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transfer Animation")
        self.resize(360, 170)

        # On active le suivi de l'ordre de selection pour que la prochaine
        # selection soit lue dans l'ordre (source en 1er, cible en 2eme).
        cmds.selectPref(trackSelectionOrder=True)

        main = qt.QWidget()
        self.setCentralWidget(main)
        container = qt.QVBoxLayout(main)

        info = qt.QLabel(
            "Selectionne d'abord la SOURCE, puis la CIBLE.\n"
            "L'animation du 1er objet est transferee sur le 2eme.\n"
            "Gere l'anim directe ET les layers d'animation."
        )
        info.setWordWrap(True)
        container.addWidget(info)

        separator(container)

        self.copy_check = qt.QCheckBox("Copier (garder l'animation sur la source)")
        container.addWidget(self.copy_check)

        container.addStretch()

        self.status = qt.QLabel("")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color: #aaaaaa;")
        container.addWidget(self.status)

        transfer_btn = qt.QPushButton("Transferer l'animation")
        transfer_btn.setFixedHeight(40)
        transfer_btn.clicked.connect(self._transfer)
        container.addWidget(transfer_btn)

    def _transfer(self):
        sel = cmds.ls(selection=True, long=True)
        if len(sel) < 2:
            cmds.warning("Selectionne d'abord la source, puis la cible (2 objets).")
            return

        for i in range(0, len(sel), 2):
            count = transferAnimation(self.copy_check.isChecked(), sel[i], sel[i + 1])
            if count:
                mode = "copie(s)" if self.copy_check.isChecked() else "deplace(s)"
                self.status.setText(f"{count} attribut(s) {mode}.")
            else:
                self.status.setText("Rien a transferer (voir le warning).")


def transferAnimation(copy: bool, source: str, target: str) -> int:
    cmds.undoInfo(openChunk=True)
    try:
        layers = _layersForNode(source)
        if layers:
            count = _transferLayers(source, target, layers, copy)
        else:
            count = _transferDirect(source, target, copy)
    finally:
        cmds.undoInfo(closeChunk=True)

    if count == 0:
        cmds.matchTransform(target, source)
    else:
        mode = "copiee" if copy else "deplacee"
        print(f"Animation {mode} : {count} attribut(s) de {source} vers {target}")

    try:
        v = cmds.getAttr(source + ".focusDistance")
        cmds.setAttr(target + ".focusDistance", v)

        v = cmds.getAttr(source + ".centerOfInterest")
        cmds.setAttr(target + ".centerOfInterest", v)

        v = cmds.getAttr(source + ".focalLength")
        cmds.setAttr(target + ".focalLength", v)

        v = cmds.getAttr(source + ".fStop")
        cmds.setAttr(target + ".fStop", v)
    except Exception as e:
        print(e)
        pass

    return count


# ---------------- cas anim directe (sans layer) ----------------
def _transferDirect(source: str, target: str, copy: bool) -> int:
    """Reconnecte (ou duplique) les animCurve branchees directement."""
    # Paires [plug_source, plug_courbe, ...] : sortie de la courbe -> attribut source.
    conns = (
        cmds.listConnections(
            source,
            source=True,
            destination=False,
            type="animCurve",
            connections=True,
            plugs=True,
        )
        or []
    )

    count = 0
    for i in range(0, len(conns), 2):
        src_plug = conns[i]  # ex: source.translateX
        curve_plug = conns[i + 1]  # ex: courbe.output
        attr = src_plug.split(".", 1)[1]
        tgt_plug = f"{target}.{attr}"

        if not _tgtReady(tgt_plug):
            continue

        if copy:
            # inputConnections=True garde les drivers (set driven keys) branches.
            curve_node = curve_plug.split(".")[0]
            new_curve = cmds.duplicate(curve_node, inputConnections=True)[0]
            cmds.connectAttr(f"{new_curve}.output", tgt_plug, force=True)
        else:
            cmds.disconnectAttr(curve_plug, src_plug)
            cmds.connectAttr(curve_plug, tgt_plug, force=True)

        count += 1

    return count


# ---------------- cas anim sur layers ----------------
def _layersForNode(node: str) -> list[str]:
    """Layers d'animation (base incluse) dont un attribut du node est membre."""
    result = []
    for layer in cmds.ls(type="animLayer") or []:
        attrs = cmds.animLayer(layer, query=True, attribute=True) or []
        if any(_sameNode(a, node) for a in attrs):
            result.append(layer)
    return result


def _transferLayers(source: str, target: str, layers: list[str], copy: bool) -> int:
    """Transfere les cles layer par layer en gardant la structure des layers.

    On inscrit d'abord la cible dans les memes layers que la source (ce qui
    cree aussi son appartenance a la base + les animBlendNode), puis on copie
    les cles de chaque attribut sur chaque layer.
    """
    base = cmds.animLayer(query=True, root=True)

    # 1) Inscrire la cible dans les layers et collecter les paires a copier.
    layer_pairs = {}  # layer -> [(src_plug, tgt_plug), ...]
    for layer in layers:
        pairs = []
        for a in cmds.animLayer(layer, query=True, attribute=True) or []:
            if not _sameNode(a, source):
                continue
            attr = a.split(".", 1)[1]
            tgt_plug = f"{target}.{attr}"
            if not _tgtReady(tgt_plug):
                continue
            # Ajouter l'attribut cible au layer (la base est geree automatiquement).
            if layer != base:
                try:
                    cmds.animLayer(layer, edit=True, attribute=tgt_plug)
                except Exception:
                    pass
            pairs.append((a, tgt_plug))
        layer_pairs[layer] = pairs

    # 2) Copier / coller les cles, layer par layer et attribut par attribut.
    count = 0
    for layer, pairs in layer_pairs.items():
        for src_plug, tgt_plug in pairs:
            if not cmds.copyKey(src_plug, animLayer=layer):
                continue
            cmds.pasteKey(tgt_plug, animLayer=layer, option="replaceCompletely")
            if not copy:
                cmds.cutKey(src_plug, animLayer=layer, clear=True)
            count += 1

    return count


# ---------------- helpers ----------------
def _tgtReady(tgt_plug: str) -> bool:
    """L'attribut cible existe-t-il et est-il modifiable ?"""
    if not cmds.objExists(tgt_plug):
        cmds.warning(
            f"Attribut absent sur la cible, ignore : {tgt_plug.split('.', 1)[-1]}"
        )
        return False
    if cmds.getAttr(tgt_plug, lock=True):
        cmds.warning(f"Attribut verrouille sur la cible, ignore : {tgt_plug}")
        return False
    return True


def _sameNode(plug: str, node: str) -> bool:
    """Le plug (ex: 'pCube1.tx') appartient-il au meme node que 'node' ?"""
    plug_node = plug.rsplit(".", 1)[0]
    if not cmds.objExists(plug_node):
        return False
    a = cmds.ls(plug_node, long=True)
    b = cmds.ls(node, long=True)
    return bool(a and b and a[0] == b[0])


def separator(layout: qt.QVBoxLayout):
    separator = qt.QFrame()
    separator.setFrameShape(qt.QFrame.HLine)
    separator.setFrameShadow(qt.QFrame.Sunken)
    separator.setStyleSheet("background-color: #555555;")
    separator.setFixedHeight(2)
    layout.addWidget(separator)
