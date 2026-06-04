import qtpy.QtWidgets as qt
import maya.cmds as cmds



class offsetShot(qt.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add  or supp frames to Shot")
        self.resize(400, 80)

        main = qt.QWidget()
        self.setCentralWidget(main)
        main_container = qt.QHBoxLayout(main)

        supp_btn = qt.QPushButton("< supp frame")
        supp_btn.clicked.connect(lambda: self._decalShot(True))
        supp_btn.setFixedHeight(40)
        supp_btn.setFixedWidth(100)
        main_container.addWidget(supp_btn)

        self.spin = qt.QSpinBox()
        self.spin.setFixedHeight(40)
        self.spin.setValue(10)
        main_container.addWidget(self.spin)

        add_btn = qt.QPushButton("add frame >")
        add_btn.clicked.connect(lambda: self._decalShot(False))
        add_btn.setFixedHeight(40)
        add_btn.setFixedWidth(100)
        main_container.addWidget(add_btn)

    def _decalShot(self, inverte: bool) -> None:
        selected_shots = cmds.ls(selection=True, type="shot")
        if not selected_shots:
            cmds.warning("No shot is selected. Please select a shot in the Camera Sequencer.")
            return
        shot_name = selected_shots[0]
        if not cmds.objExists(shot_name) or cmds.nodeType(shot_name) != "shot":
            return
        sequence = cmds.listConnections(shot_name, type="sequencer")
        if not sequence:
            return
        
        offset = self.spin.value()
        if inverte:
            offset = offset.__invert__() + 1
        
        self.applyOffsetOnShotName(offset, shot_name, sequence)
        self.applyOffsetOnKey(offset)

    def applyOffsetOnShotName(self, offset: int, shot_name: str, sequence: str):
        all_shots = cmds.listConnections(f"{sequence}.shots", source=True) or []
        all_shots.sort(key=lambda x: cmds.getAttr(f"{x}.sequenceStartFrame"))

        end_frame = cmds.getAttr(f"{shot_name}.endFrame")
        current_track = cmds.getAttr(f"{shot_name}.track")
        sequence_start = cmds.getAttr(f"{shot_name}.sequenceStartFrame")
        new_end_frame = end_frame + offset

        cmds.shot(shot_name, e=True, endTime=new_end_frame)
        cmds.setAttr(f"{shot_name}.sequenceStartFrame", sequence_start)
        cmds.setAttr(f"{shot_name}.track", current_track)

        cumulative_offset = offset
        current_shot_index = all_shots.index(shot_name)
        for i in range(current_shot_index + 1, len(all_shots)):
            next_shot = all_shots[i]
            next_start = cmds.getAttr(f"{next_shot}.startFrame")
            next_end = cmds.getAttr(f"{next_shot}.endFrame")
            next_sequence_start = cmds.getAttr(f"{next_shot}.sequenceStartFrame")
            next_track = cmds.getAttr(f"{next_shot}.track")

            new_sequence_start = next_sequence_start + cumulative_offset
            cmds.shot(next_shot, e=True, startTime=next_start + cumulative_offset, endTime=next_end + cumulative_offset)
            cmds.setAttr(f"{next_shot}.sequenceStartFrame", new_sequence_start)
            cmds.setAttr(f"{next_shot}.track", next_track)

    def applyOffsetOnKey(offset, start_frame):
        start_frame = cmds.currentTime(query=True)
        anim_curves = cmds.ls(type="animCurve")
        if not anim_curves:
            cmds.warning("Aucune courbe d'animation trouvée dans la scène.")
            return

        for curve in anim_curves:
            try:
                # Vérifier les clés à partir de la frame courante
                keys = cmds.keyframe(curve, query=True, timeChange=True)
                if keys:
                    keys_to_shift = [k for k in keys if k >= start_frame]
                    if keys_to_shift:
                        cmds.keyframe(curve, edit=True, time=(min(keys_to_shift), max(keys_to_shift)), relative=True, timeChange=offset)
                        print(f"Clés déplacées pour {curve} à partir de {start_frame}.")
            except RuntimeError as e:
                cmds.warning(f"Erreur lors du déplacement des clés pour {curve}: {e}")
