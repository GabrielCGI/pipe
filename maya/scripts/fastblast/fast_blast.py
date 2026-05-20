from maya import cmds
from maya import mel

import os
from pathlib import Path
import re
import subprocess

from . import get_shotlist 
from .fast_blast_UI import FastBlastUI

_PRODUCTION_IDENTIFIER = "03_Production"
_BLAST_PRIO = ["Anim", "AnimSpline", "AnimBlock", "Layout", "previz", "animatic"]
RV_BIN = r"C:\ILLOGIC_APP\OpenRV\bin\rv.exe"

class FastBlast:
    def __init__(self, ui:FastBlastUI):
        self.display_mask = None

        # initialize values to be stored once per ui launch
        self.user = self.get_user()
        self.project_root, self.project, self.sequence, self.shot, self.anim_type = self.get_shot_name()
        self.shot_order = get_shotlist.get_shot_order(self.project)

        self.blast_name = self.get_blast_name()
        self.filename = self.get_dirname()

        self.ui = ui

    def get_user(self):
        return os.getlogin()

    def get_dirname(self):
        base = rf"C:\Users\{self.user}\Documents\tmp_ILLOGIC"

        shot_data_ok = all([self.project, self.sequence, self.shot, self.anim_type])

        if not shot_data_ok:
            dirpath = os.path.join(base, "tmp")
            os.makedirs(dirpath, exist_ok=True)
            return os.path.join(dirpath, self.blast_name)

        dirpath = os.path.join(base, self.project, self.sequence, self.anim_type)
        os.makedirs(dirpath, exist_ok=True)
        return os.path.join(dirpath, self.blast_name)

    def get_blast_name(self):

        shot_data_ok = all([self.sequence, self.shot])
        if not shot_data_ok:
            name = cmds.file(q=True, sn=True)
            name = os.path.basename(name)
            if not name: 
                return "unnamed_WIPBlast.mov"
            return f"{name}_WIPBlast.mov"
        
        return f"{self.sequence}-{self.shot}_{self.anim_type}_WIPBlast.mov"

    def get_cam(self):
        # TODO: Get the proper cam using what fred showed

        if self.keep_current_cam:
            camera = cmds.modelPanel(self.current_panel, q=True, camera=True)
            if camera:
                return camera

        cam_list = cmds.listCameras()
        camera = ""

        for cam in cam_list:
            if "shotCam" in cam:
                if camera:
                    print("Two shotCam exist, currently not handled")
                camera = cam

        if not camera:
            camera = cam_list[0]

        return camera

    def get_shot_name(self):
        scene_path = cmds.file(q=True, sn=True)
        scene_path = Path(scene_path)

        # I:/Production/03_Production/Shots
        try:
            production_index = scene_path.parts.index(_PRODUCTION_IDENTIFIER)
        except ValueError:
            print(
                f'File not in prism project, cant get previous/next shots:\n - "{scene_path.as_posix()}"',
            )
            return "","","","",""

        project_root = Path(*scene_path.parts[: production_index + 2])
        project = scene_path.parts[production_index - 1]
        sequence = scene_path.parts[production_index + 2]
        shot = scene_path.parts[production_index + 3]
        anim_type = scene_path.parent.name

        return project_root, project, sequence, shot, anim_type

    def get_current_shot_index(self):
        shot_full_name = self.sequence + "/" + self.shot

        if shot_full_name in self.shot_order:
            return self.shot_order.index(shot_full_name)
        
        return -1

    def get_audio_file(self):
        playback_slider = mel.eval("$tmpVar=$gPlayBackSlider")
        sound = cmds.timeControl(playback_slider, q=True, sound=True)
        return sound

    def get_latest_blast_dir(self, item: Path):
        """Get the latest existing playblast, (e.g if there are 5 versions, get v005)

        Args:
            item (Path): Path to dir containing playblast directories

        Returns:
            Path: Path to latest playblast dir
        """
        dirname = item.name
        for playblast_id in _BLAST_PRIO:
            if dirname == playblast_id:
                blast = [i for i in item.iterdir() if "mp4" not in str(i)][
                    -1
                ]  # Latest version that is not a burnin
                return blast
        return None

    def parse_blast_files(self, blast_dir: Path):
        """Parse files in a playblast directory

        Args:
            blast_dir (Path): Path to playblast directory

        Raises:
            ValueError: If no files found

        Returns:
            str: String of all files to add to the playblast in openRV compatible format
        """
        files = list(blast_dir.iterdir())

        # Check for mp4 first (highest priority)
        mp4_files = [f for f in files if f.suffix.lower() == ".mp4"]
        if mp4_files:
            mp4 = sorted(mp4_files)[-1]
            return mp4

        # Otherwise parse frame sequences
        frame_sequence = [
            f for f in files if f.is_file() and self._is_valid_frame_sequence(f)
        ]
        frame_sequence = sorted(frame_sequence)

        # old
        first = str(frame_sequence[0])
        last = str(frame_sequence[-1])

        filename = os.path.basename(first)

        # match = re.match(r"^(.+?)([._-])(\d+)(\.\w+)$", filename)
        match = re.match(r"^(.+?)(\d+)(\.\w+)$", filename)
        if not match:
            raise ValueError(f"Cannot detect frame number in: {filename}")

        base, digits, ext = match.groups()
        padding = len(digits)

        def frame_num(p):
            return int(re.search(r"(\d+)" + re.escape(ext) + r"$", p).group(1))

        first_num = frame_num(first)
        last_num = frame_num(last)

        rv_pattern = Path(blast_dir, f"{base}{'#' * padding}{ext}")
        return f"{rv_pattern} {first_num}-{last_num}"

    def _is_valid_frame_sequence(self, file: Path):
        # Check if name is a valid name sequence, e.g SEQ_basketPark-SH210_Anim_v004.0998.jpg
        name = file.stem
        parts = name.rsplit(".", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return file.suffix.lower() in [".png", ".jpg", ".exr"]
        return False

    def get_neighboring_shots(self, shot_count : int):
        """Get all shots before or after the current by the number specified.

        Args:
            shot_count (int): Number of shots before(negative shot_count) or after (positive shot_count) to get

        Returns:
            list[Path]: list of the full path for the shots 
        """
        current_shot_index = self.get_current_shot_index()
        if current_shot_index < 0 :
            return [] 
        
        neighboring_playblasts = []

        if shot_count < 0:
            inf = shot_count
            sup = 0
        else:
            inf = 1
            sup = shot_count + 1

        for i in range(inf, sup):
            shot_id = current_shot_index + i

            if shot_id >= len(self.shot_order) or shot_id < 0:
                continue

            shot = Path(self.project_root, self.shot_order[shot_id])

            playblast_dir = Path(shot, "Playblasts")

            if not playblast_dir.is_dir():
                continue

            for item in playblast_dir.iterdir():
                blast_dir = self.get_latest_blast_dir(item)
                if blast_dir:
                    blast = self.parse_blast_files(blast_dir)
                    neighboring_playblasts.append(blast)

        return neighboring_playblasts

    def get_model_editor_setting(self, in_editor="", new_editor=""):
        """Get the model editor's settings, applicable to our new editor

        Args:
            in_editor (str): Name of the editor to get the editor's settings from
            new_editor (str): Name of the new editor we'd like those settings applied to

        Returns:
            str: StateString, mel commands necessary to apply viewport settings to our model editor
        """

        print("getModelEditorSetting()")
        stateString = cmds.modelEditor(in_editor, q=1, stateString=True)

        stateString = stateString.replace("$editorName", new_editor)
        stateString = re.sub("(?<=camera ).*", self.camera, stateString)

        return stateString

    def create_playblast_view(self):
        """Create a maya view for the playblast"""

        self.model_panel_name = "wipPlayBlastModelPanel"

        # if panel exists, remove it
        if cmds.modelPanel(self.model_panel_name, exists=True):
            cmds.deleteUI(self.model_panel_name, panel=True)

        # Create window
        self.maya_window = cmds.window(
            title="FastBlast Playblast View", widthHeight=(2048, 2048)
        )
        form = cmds.formLayout()

        self.test_mp = cmds.modelPanel(
            self.model_panel_name, label="PlayblastView", menuBarVisible=False
        )

        # Stretch the panel to fill the entire formLayout
        cmds.formLayout(
            form,
            edit=True,
            attachForm=[
                (self.test_mp, "top", 0),
                (self.test_mp, "left", 0),
                (self.test_mp, "bottom", 0),
                (self.test_mp, "right", 0),
            ],
        )

        self.created_editor = cmds.modelPanel(self.test_mp, q=True, modelEditor=True)
        print(f"Model panel : {self.test_mp}, model editor : {self.created_editor}")

        self.current_panel = cmds.getPanel(withFocus=True)
        self.camera = self.get_cam()

        self.display_mask = cmds.camera(self.camera, query=True, displayGateMask=True)
        print("Mask :", self.display_mask)
        cmds.camera(self.camera, e=True, displayGateMask=True)

        # Apply camera and display settings via the editor
        cmds.modelPanel(self.test_mp, edit=True, camera=self.camera)
        if self.keep_current_vp_settings:
            state_string = self.get_model_editor_setting(
                self.current_panel, self.test_mp
            )
            mel.eval(state_string)
        else:
            cmds.modelEditor(
                self.created_editor,
                edit=True,
                displayAppearance="smoothShaded",
                displayTextures=True,
                # Curves & Surfaces
                dimensions=False,
                nurbsCurves=False,
                nurbsSurfaces=True,
                controlVertices=False,
                hulls=False,
                polymeshes=True,
                subdivSurfaces=True,
                # Fx
                dynamics=True,
                dynamicConstraints=False,
                fluids=True,
                follicles=False,
                hairSystems=True,
                nCloths=True,
                nParticles=True,
                nRigids=True,
                particleInstancers=False,
                # Rig & Anim
                clipGhosts=False,
                controllers=False,
                deformers=False,
                handles=False,
                ikHandles=False,
                joints=False,
                locators=False,
                motionTrails=False,
                pivots=False,
                # Lighting, shading & rendering
                cameras=False,
                planes=False,
                lights=False,
                strokes=False,
                useRGBImagePlane=False,
                # Viewport utils
                headsUpDisplay=False,
                holdOuts=False,
                grid=False,
                selectionHiliteDisplay=False,
                # Plugins
                bluePencil=False,
                pluginShapes=False,
            )

        # cmds.showWindow(self.maya_window)
        cmds.refresh()

    def create_playblast(self):
        """Create playblast parameters chosen"""

        print(f"Saving to: {self.filename}")

        width = cmds.getAttr("defaultResolution.width")
        height = cmds.getAttr("defaultResolution.height")

        print(f"Camera selected: {self.camera}")

        playblast = cmds.playblast(
            editorPanelName=self.created_editor,
            viewer=False,
            offScreen=True,
            format="qt",
            compression="h264",
            quality=100,
            percent=100,
            filename=self.filename,
            forceOverwrite=True,
            sound=self.get_audio_file(),
            widthHeight=[width, height],
        )

        print(f"Created blast {playblast}")

        if self.display_mask is not None:
            cmds.camera(self.camera, e=True, displayGateMask=self.display_mask)

        if self.maya_window:
            print("Deleting UI")
            cmds.deleteUI(self.maya_window)

        return playblast

    def open_in_rv(self, clips: list, fps=None, additional_args=None):
        """Open playblast in openRV, combining it with all selected next and previous shots

        Args:
            clips (list[str]): list of openRV compatible strings for the paths
            fps (str, optional): Parameter allowing us to select fps
            additional_args (str, optional): any additional params

        Raises:
            ValueError: No clips to blast
            FileNotFoundError: Files descibed not found
        """
        if not clips:
            raise ValueError("No clips provided.")

        missing_videos = [
            c
            for c in clips
            if not ("#" in c or os.path.isdir(c)) and not os.path.exists(c)
        ]

        if missing_videos:
            raise FileNotFoundError("Missing files:\n" + "\n".join(missing_videos))

        cmd = [RV_BIN]
        cmd += clips

        if fps is not None:
            cmd += ["-fps", str(fps)]

        if additional_args:
            cmd += additional_args

        print(f"[RV] Launching:\n  {' '.join(cmd)}")
        subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        print("RV launched successfully")

    def open_test(self, file=""):
            print("open_test()")
            if os.path.isfile(file) in [True,1] :
                print("\t Blast_Path exists:",file)
                try :
                    os.remove (file)
                    print("\t removed")
                except Exception as err:
                    print(Exception,err)
                    self.ui.touch_warning()

    def run(self, prev=0, next=0, keep_cam=False, keep_vp_settings=False):

        self.keep_current_cam = keep_cam
        self.keep_current_vp_settings = keep_vp_settings

        self.previous_shots = self.get_neighboring_shots(prev)
        self.next_shots = self.get_neighboring_shots(next)

        self.open_test(self.filename)

        self.create_playblast_view()
        self.genereated_playblast = self.create_playblast()

        clips = []
        clips.extend(self.previous_shots)
        clips.append(self.genereated_playblast)
        clips.extend(self.next_shots)

        clips = [str(i) for i in clips]
        self.open_in_rv(clips)
