import qtpy.QtWidgets as qt
import qtpy.QtGui as qtg
import maya.cmds as cmds
import re
import os


from .edit_camera import createFreeCamFromRig


SHOT_PREFIX = "SH"
SEQ_PREFIX = "SQ"
CAM_PREFIX = "cam"
LAY_PREFIX = "lay"
PADDING = 4
PROJET = "I:/frederic_2603"

TIME_CURVE_TYPES = ("animCurveTA", "animCurveTL", "animCurveTU", "animCurveTT")
# Zone temporaire (tres loin de toute anim plausible) ou on parke les cles
# pendant le retime pour eviter toute collision entre plages.
KEY_BUFFER_BASE = 1000000.0
KEY_BUFFER_STEP = 1000000.0


class ManageShotsSequence(qt.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_itemCards: list["ItemCard"] = []
        self.list_shot_to_delete: list[str] = []

        self.setWindowTitle("Multi Shot edit or create")
        self.resize(420, 500)

        main = qt.QWidget()
        self.setCentralWidget(main)
        main_container = qt.QVBoxLayout(main)

        layout_parameter = qt.QVBoxLayout()
        main_container.addLayout(layout_parameter)

        st_l = qt.QLabel("Global Settings:")
        layout_parameter.addWidget(st_l)

        self.SQ_name = ligneParameter("SQ<name>: ", layout_parameter)
        self.shot_start = ligneParameter("Shot Start: ", layout_parameter)
        self.shot_start.setText("0010")

        ligne_check = qt.QHBoxLayout()
        layout_parameter.addLayout(ligne_check)

        lab = qt.QLabel("FreeCam Mode")
        lab.setMaximumWidth(130)
        ligne_check.addWidget(lab)

        self.freeCam_mode = qt.QCheckBox("add new cam with FreeCam Mode")
        self.freeCam_mode.setMaximumWidth(200)
        ligne_check.addWidget(self.freeCam_mode)

        separator(layout_parameter)

        add_shot = qt.QPushButton("Add new Shot")
        add_shot.clicked.connect(self._addNewShot)
        layout_parameter.addWidget(add_shot)

        scroller = qt.QScrollArea()
        scroller.setWidgetResizable(True)
        main_container.addWidget(scroller)
        scrolWidget = qt.QWidget()
        scroller.setWidget(scrolWidget)

        self.lay_list_shot_item = qt.QVBoxLayout(scrolWidget)

        create_shots = qt.QPushButton("Create/Rebuild Sequence")
        create_shots.clicked.connect(self._createSequence)
        main_container.addWidget(create_shots)

        # lister les shot existant dans le sequencer
        shot = None
        shots = cmds.sequenceManager(lsh=True) or []
        for shot in sorted(
            shots, key=lambda s: cmds.shot(s, q=True, sequenceStartTime=True)
        ):
            card = ItemCard(shot, True, self)
            self.lay_list_shot_item.addWidget(card)
            self.all_itemCards.append(card)

        self.lay_list_shot_item.addStretch()
        if shot is not None:
            self.SQ_name.setText(re.sub("[^0-9]", "", card.sequence))

    def _addNewShot(self):
        seq = self.SQ_name.text().strip()
        if not seq:
            cmds.warning("no sequence name give.")
            return

        start_shot = "0010"
        if not self.all_itemCards:
            start_shot = self.shot_start.text()
            new_shot = self._convertintShotToStr(start_shot, False)
        else:
            start_shot = self.all_itemCards[-1].new_shot_name.text()
            new_shot = self._convertintShotToStr(start_shot)

        card = ItemCard(f"SQ{seq}_{new_shot}", False, self)
        self.lay_list_shot_item.insertWidget(self.lay_list_shot_item.count() - 1, card)
        self.all_itemCards.append(card)

    def _convertintShotToStr(self, name: str, add=True) -> str:
        shot = re.sub("[^0-9]", "", name)
        if not shot:
            shot = "0"
        int_shot = int(shot)
        if add:
            int_shot = int_shot + 10

        return SHOT_PREFIX + str(int_shot).zfill(PADDING)

    def _deleteShot(self, item_card: "ItemCard"):
        if item_card not in self.all_itemCards:
            cmds.warning("shot not found !")
            return

        self.list_shot_to_delete.append(item_card.long_name)
        self.all_itemCards.remove(item_card)
        item_card.setParent(None)
        item_card.deleteLater()
        self.reloadUI()

    def _topCard(self, item_card: "ItemCard"):
        if item_card not in self.all_itemCards:
            cmds.warning("shot not found !")
            return

        index = self.all_itemCards.index(item_card)
        if index == 0:
            return

        self.all_itemCards.remove(item_card)
        self.all_itemCards.insert(index - 1, item_card)
        self.reloadUI()

    def _botCard(self, item_card: "ItemCard"):
        if item_card not in self.all_itemCards:
            cmds.warning("shot not found !")
            return

        index = self.all_itemCards.index(item_card)
        if index >= len(self.all_itemCards) - 1:
            return

        self.all_itemCards.remove(item_card)
        self.all_itemCards.insert(index + 1, item_card)
        self.reloadUI()

    def reloadUI(self):
        while self.lay_list_shot_item.count():
            item = self.lay_list_shot_item.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        for card in self.all_itemCards:
            self.lay_list_shot_item.addWidget(card)

        self.lay_list_shot_item.addStretch()

    def _validateNames(self) -> bool:
        managed_shots = {c.long_name for c in self.all_itemCards}
        managed_ns = {c.nameSpace for c in self.all_itemCards if c.nameSpace}

        seen_shots = set()
        for card in self.all_itemCards:
            if not card.new_shot_name.text().strip():
                cmds.warning("Un shot n'a pas de nom.")
                return False

            new_name = card.getNewShotName()
            if new_name in seen_shots:
                cmds.warning(f"Deux shots portent le meme nom : {new_name}")
                return False
            seen_shots.add(new_name)

            if new_name not in managed_shots and cmds.objExists(new_name):
                cmds.warning(f"Un objet '{new_name}' existe deja dans la scene.")
                return False

            ns = card.getNameSpaceCam()
            if ns not in managed_ns and cmds.namespace(exists=ns):
                cmds.warning(f"Le namespace '{ns}' existe deja.")
                return False

        return True

    def _createSequence(self):
        if not self._validateNames():
            return

        if self.list_shot_to_delete:
            result = qt.QMessageBox.warning(
                self,
                "do you want save",
                "vous voulez supprimer un shot de votre sequence\n voulez vous save votre scene avant d'executer le code",
                qt.QMessageBox.Yes | qt.QMessageBox.No | qt.QMessageBox.Cancel,
                qt.QMessageBox.Cancel,
            )
            if result == qt.QMessageBox.Cancel:
                return
            if result == qt.QMessageBox.Yes:
                cmds.file(save=True)

            self._deleteShotsInScene()

        path_camRig = (
            self._findPathCamera()
        )  # trouver le chemin de la référence de la camera pour pouvoir l'importer
        if path_camRig is None:
            return

        freeCam_mode = (
            self.freeCam_mode.isChecked()
        )  # savoir si les camera seront creer en freeMode ou pas

        # 1) Precalcule la nouvelle plage de chaque shot et, pour les shots
        #    existants, releve leur ancienne plage scene AVANT toute modif.
        retime_ops = []  # (old_start, old_end, new_start, new_end)
        frame = 1001
        for card in self.all_itemCards:
            card.new_start = frame
            card.new_end = frame + card.geteNewDuration() - 1

            if cmds.objExists(card.long_name):
                old_start = cmds.shot(card.long_name, q=True, st=True)
                old_end = cmds.shot(card.long_name, q=True, et=True)
                retime_ops.append((old_start, old_end, card.new_start, card.new_end))

            frame += card.geteNewDuration()

        # 2) Retime les cles d'animation pour suivre les shots (offset + scale).
        self._retimeKeys(retime_ops)

        # 3) Cree / renomme les shots, cameras et groupes lay_.
        for card in self.all_itemCards:
            if not cmds.objExists("|MasterLayout"):
                cmds.createNode("transform", n="|MasterLayout", ss=True)
            if not cmds.objExists("|cameras"):
                cmds.createNode("transform", n="|cameras", ss=True)

            # importer la référence de la camera dans la scene
            if not cmds.objExists(card.cam_link):
                new_nodes = cmds.file(
                    path_camRig,
                    reference=True,
                    namespace=card.getNameSpaceCam(),
                    returnNewNodes=True,
                )
                ref_node = cmds.referenceQuery(new_nodes[0], referenceNode=True)
                root_nodes = self._getRootNodeReference(ref_node)
                if root_nodes:
                    cmds.parent(root_nodes, "|cameras")

                if freeCam_mode:
                    cmds.select(f"{card.getNameSpaceCam()}:shotCam")
                    createFreeCamFromRig()

            else:
                if card.cam_link != card.getNewCamName():
                    ref_file = cmds.referenceQuery(card.cam_link, filename=True)
                    cmds.file(ref_file, edit=True, namespace=card.getNameSpaceCam())

            # creer les different shot dans le shot sequencer
            if not cmds.objExists(card.long_name):
                cmds.shot(
                    card.getNewShotName(),
                    set=str(card.new_end),
                    sst=str(card.new_start),
                    et=str(card.new_end),
                    st=str(card.new_start),
                    s=1.0,
                    mute=card.getNewMuted(),
                )
                cmds.shot(card.getNewShotName(), e=True, cc=card.getNewCamName())
            else:
                if card.long_name != card.getNewShotName():
                    cmds.rename(card.long_name, card.getNewShotName())

                cmds.shot(card.getNewShotName(), e=True, set=card.new_end)
                cmds.shot(card.getNewShotName(), e=True, sst=card.new_start)
                cmds.shot(card.getNewShotName(), e=True, et=card.new_end)
                cmds.shot(card.getNewShotName(), e=True, st=card.new_start)
                cmds.shot(card.getNewShotName(), e=True, s=1.0)
                cmds.shot(card.getNewShotName(), e=True, cc=card.getNewCamName())
                cmds.shot(card.getNewShotName(), e=True, sn=card.getNewShotName())
                cmds.shot(card.getNewShotName(), e=True, mute=card.getNewMuted())

            # creer les different grp pour les layout par shot
            if not cmds.objExists(f"|MasterLayout|{LAY_PREFIX}_{card.long_name}"):
                cmds.createNode(
                    "transform",
                    n=f"{LAY_PREFIX}_{card.getNewShotName()}",
                    ss=True,
                    p="|MasterLayout",
                )
            else:
                cmds.rename(
                    f"{LAY_PREFIX}_{card.long_name}",
                    f"{LAY_PREFIX}_{card.getNewShotName()}",
                )

        # re étalonner tout les shot sur la v001
        for card in self.all_itemCards:
            cmds.shot(card.getNewShotName(), e=True, track=1)

    def _retimeKeys(self, retime_ops: list):
        if not retime_ops:
            return

        curves = cmds.ls(type=TIME_CURVE_TYPES) or []
        if not curves:
            return

        # Passe 1 : ancienne plage -> tampon unique (offset pur, longueur conservee).
        temp_ops = []  # (temp_start, temp_end, new_start, new_end)
        for i, (old_start, old_end, new_start, new_end) in enumerate(retime_ops):
            temp_start = KEY_BUFFER_BASE + i * KEY_BUFFER_STEP
            temp_end = temp_start + (old_end - old_start)
            self._remapKeys(curves, old_start, old_end, temp_start, temp_end)
            temp_ops.append((temp_start, temp_end, new_start, new_end))

        # Passe 2 : tampon -> nouvelle plage finale (offset + scale).
        for temp_start, temp_end, new_start, new_end in temp_ops:
            self._remapKeys(curves, temp_start, temp_end, new_start, new_end)

        # Passe 3 : le scale a pu produire des cles sur des frames decimales,
        # on les recale sur des frames entieres.
        cmds.snapKey(curves, timeMultiple=1)

    def _deleteShotsInScene(self):
        # supprime de la scene tous les shots marques pour suppression
        # (cf. _deleteShot qui empile leur long_name dans list_shot_to_delete).
        for shot_name in self.list_shot_to_delete:
            if not cmds.objExists(shot_name):
                continue

            try:
                # camera liee + plage temporelle du shot a relever AVANT toute suppression.
                cam = cmds.shot(shot_name, q=True, cc=True)
                start = cmds.shot(shot_name, q=True, st=True)
                end = cmds.shot(shot_name, q=True, et=True)

                # 1) supprimer le shot dans le sequencer
                cmds.delete(shot_name)

                # 2) purger les cles d'animation comprises dans la plage du shot,
                #    pour tous les objets animes de la scene.
                self._deleteKeysInRange(start, end)

                # 3) supprimer le groupe layout associe (|MasterLayout|lay_<shot>)
                lay_grp = f"|MasterLayout|{LAY_PREFIX}_{shot_name}"
                if cmds.objExists(lay_grp):
                    cmds.delete(lay_grp)

                # 4) supprimer la camera (reference + freeCam eventuelle + namespace)
                if cam and cmds.objExists(cam):
                    self._deleteCamera(cam)
            except Exception as e:
                cmds.warning(f"Suppression du shot '{shot_name}' impossible : {e}")

        self.list_shot_to_delete.clear()

    def _deleteCamera(self, cam: str):
        namespace = cam.split("|")[-1].split(":")[0] if ":" in cam else None

        # retirer la reference de la camera
        if cmds.referenceQuery(cam, isNodeReferenced=True):
            ref_node = cmds.referenceQuery(cam, referenceNode=True)
            cmds.file(removeReference=True, referenceNode=ref_node)

        # supprimer le contenu local restant (ex: freeCam) puis le namespace devenu inutile
        if namespace and cmds.namespace(exists=namespace):
            cmds.namespace(removeNamespace=namespace, deleteNamespaceContent=True)

    def _deleteKeysInRange(self, start, end):
        curves = cmds.ls(type=TIME_CURVE_TYPES) or []
        if not curves:
            return

        # clear=True : on retire les cles sans les copier dans le presse-papier.
        cmds.cutKey(curves, time=(start, end), clear=True)

    def _findPathCamera(self) -> str | None:
        path_product = f"{PROJET}/03_Production/Assets/Cameras/camRig/Export/Rigging"
        if not os.path.exists(path_product):
            return None

        versions = sorted(
            d
            for d in os.listdir(path_product)
            if os.path.isdir(os.path.join(path_product, d))
        )
        if not versions:
            return None

        folder_version = versions[-1]
        path_to_import = (
            f"{path_product}/{folder_version}/camRig_Rigging_{folder_version}"
        )
        for ext in [".mb", ".ma"]:
            if os.path.exists(path_to_import + ext):
                return path_to_import + ext

        return None

    def _getRootNodeReference(self, referenceNode: str):
        all_nodes = cmds.referenceQuery(referenceNode, nodes=True, dp=True)
        if not all_nodes:
            return []

        sel_nodes = [
            n
            for n in all_nodes
            if cmds.nodeType(n) == "transform" and not n.count("|") >= 2
        ]
        if not sel_nodes:
            return []

        all_nodes_root = []
        for root in sel_nodes:
            name = cmds.listRelatives(root, parent=True, fullPath=True)
            if name is None:
                all_nodes_root.append(root)
                continue

            if not cmds.referenceQuery(name, isNodeReferenced=True):
                all_nodes_root.append(root)

        return all_nodes_root

    def _remapKeys(self, curves, src_start, src_end, dst_start, dst_end):
        if src_end == src_start:
            cmds.keyframe(
                curves,
                edit=True,
                time=(src_start, src_end),
                relative=True,
                timeChange=dst_start - src_start,
            )
        else:
            cmds.scaleKey(
                curves,
                time=(src_start, src_end),
                newStartTime=dst_start,
                newEndTime=dst_end,
            )


class ItemCard(qt.QFrame):
    def __init__(self, long_name: str, exist: bool, parent: "ManageShotsSequence"):
        super().__init__()
        self.parent_UI = parent
        self.long_name = long_name
        self.sequence = long_name.split("_")[0]
        self.shot_name = long_name.split("_")[1]
        self.nameSpace = self._NameSpaceCam()
        self.duration = self._setDuration()
        self.cam_link = self._setCamera()
        self.is_muted = self._muted()
        self.new_start = None
        self.new_end = None
        self.exist = exist

        # start UI
        container = qt.QVBoxLayout(self)

        ligne_edit = qt.QHBoxLayout()
        container.addLayout(ligne_edit)
        ligne_edit.setContentsMargins(0, 0, 0, 0)

        name_label = qt.QLabel(self.long_name)
        ligne_edit.addWidget(name_label)

        ligne_edit.addStretch()

        got_top = qt.QPushButton("top")
        got_top.clicked.connect(lambda: self.parent_UI._topCard(self))
        ligne_edit.addWidget(got_top)

        got_bot = qt.QPushButton("bot")
        got_bot.clicked.connect(lambda: self.parent_UI._botCard(self))
        ligne_edit.addWidget(got_bot)

        self.mute = qt.QCheckBox("Mute Shot")
        self.mute.setChecked(self.is_muted)
        self.mute.toggled.connect(self._mute_interface)
        ligne_edit.addWidget(self.mute)

        supp = qt.QPushButton("X")
        supp.setStyleSheet(self._styleSupp())
        supp.clicked.connect(lambda: self.parent_UI._deleteShot(self))
        supp.setFixedSize(24, 24)
        ligne_edit.addWidget(supp)

        separator(container)

        self.new_shot_name = ligneParameter("shot name: ", container, False)
        self.new_shot_name.setText(self.shot_name)

        self.new_duration = ligneParameter("duration Shot: ", container)
        self.new_duration.setText(str(self.duration))

        cam_link = ligneParameter("camera used: ", container, False, False)
        cam_link.setText(self.cam_link)

        self._mute_interface(self.is_muted)

    def _setCamera(self) -> str:
        if cmds.objExists(self.long_name):
            cam = cmds.shot(self.long_name, q=True, cc=True)
            if not cam:
                cam = f"{CAM_PREFIX}_{self.long_name}:shotCam"
            return cam
        else:
            return f"{CAM_PREFIX}_{self.long_name}:shotCam"

    def _setDuration(self) -> int:
        if cmds.objExists(self.long_name):
            return (
                int(
                    cmds.shot(self.long_name, q=True, set=True)
                    - cmds.shot(self.long_name, q=True, sst=True)
                )
                + 1
            )
        else:
            return 20

    def _NameSpaceCam(self) -> str | None:
        if ":" not in self._setCamera():
            return None

        return self._setCamera().split("|")[-1].split(":")[0]

    def _muted(self) -> bool:
        if cmds.objExists(self.long_name):
            return cmds.shot(self.long_name, q=True, mute=True)

        return False

    def _mute_interface(self, mute: bool):
        self.is_muted = mute

        self.new_shot_name.setDisabled(mute)
        self.new_duration.setDisabled(mute)
        self._CustomStyle()

    def getNewShotName(self) -> str:
        return f"{self.sequence}_{self.new_shot_name.text()}"

    def geteNewDuration(self) -> int:
        return int(self.new_duration.text())

    def getNewCamName(self) -> str:
        return f"{self.getNameSpaceCam()}:shotCam"

    def getNameSpaceCam(self) -> str:
        return f"{CAM_PREFIX}_{self.getNewShotName()}"

    def getNewMuted(self) -> bool:
        return self.mute.isChecked()

    def _CustomStyle(self):
        if self.is_muted:
            self.setStyleSheet("""
            QFrame{
                background: #333333;
                border: 1px solid #666666;
                border-radius: 6px;
            }
            QLabel{
                border: none;
            }
            QLineEdit{
                border: none;
            }""")
        else:
            self.setStyleSheet("""
            QFrame{
                border: 1px solid #666666;
                border-radius: 6px;
            }
            QLabel{
                border: none;
            }
            QLineEdit{
                border: none;
            }""")

        self.repaint()

    def _styleSupp(self):
        return """
        QPushButton{
            background: #330000; 
            border: 1px solid #660000; 
            border-radius: 4px;
        }
        QPushButton::selected{
            background: #660000; 
            border: 1px solid #AA5555; 
        }
        QPushButton::hover{
            background: #660000; 
            border: 1px solid #AA5555; 
        }
        """


def ligneParameter(name, layout: qt.QVBoxLayout, vent=True, edit=True) -> qt.QLineEdit:
    ligne = qt.QHBoxLayout()
    layout.addLayout(ligne)

    tt = qt.QLabel(name)
    tt.setMaximumWidth(130)
    ligne.addWidget(tt)

    parm = qt.QLineEdit() if edit else qt.QLabel()
    if vent:
        parm.setValidator(qtg.QIntValidator(0, 9999))
    parm.setMaximumWidth(200)
    ligne.addWidget(parm)

    return parm


def separator(layout: qt.QVBoxLayout):
    separator = qt.QFrame()
    separator.setFrameShape(qt.QFrame.HLine)
    separator.setFrameShadow(qt.QFrame.Sunken)
    separator.setStyleSheet("background-color: #555555;")
    separator.setFixedHeight(2)
    layout.addWidget(separator)
