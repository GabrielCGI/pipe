from importlib import reload
from pathlib import Path
import traceback
import getpass
import os
import re



import Prism_prepPlayBlast_monkeypatch as monkeypatch
import burnIn_maya
reload(monkeypatch)
reload(burnIn_maya)



class Prism_prepPlayBlast_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.settings_default_maya = {}
        self.settings_header_display = {}
        self.outputFile = None
        self.cam_check = []
        if self.core.appPlugin.pluginName not in ["Maya"]:
            return
        
        self.core.registerCallback("prePublish", self.prePublish, plugin=self)
        self.core.registerCallback("postPublish", self.postPublish, plugin=self)
        self.core.registerCallback("postPlayblast", self.postPlayblast, plugin=self)

        shotGridplugin = self.core.getPlugin("Shotgrid")
        self.monkey = monkeypatch.MonkeyPatchSG(core)
        prjplug = shotGridplugin.prjMng
        if prjplug:
            self.core.plugins.monkeyPatch(prjplug.createUploadableMedia, self.monkey.createUploadableMedia, plugin, force=True)
        

    # ----------------------------- hooks -----------------------------
    def prePublish(self, *args, **kwargs) -> None:
        import maya.cmds as cmds #type: ignore


        cmds.select(clear=True)
        for panel in cmds.getPanel(type="modelPanel"):
            settings_panel = {}
            cam_shape = cmds.modelEditor(panel, q=True, camera=True)
            
            
            #store panel data
            settings_panel["camera"] = cam_shape
            settings_panel["allObjects"] = cmds.modelEditor(panel, q=True, allObjects=False) or True
            settings_panel["wireframeOnShaded"] = cmds.modelEditor(panel, q=True, wireframeOnShaded=False)
            settings_panel["pluginShapes"] = cmds.modelEditor(panel, q=True, pluginShapes=True)
            settings_panel["nurbsCurves"] = cmds.modelEditor(panel, q=True, nurbsCurves=True)
            settings_panel["polymeshes"] = cmds.modelEditor(panel, q=True, polymeshes=True)
            settings_panel["grid"] = cmds.modelEditor(panel, q=True, grid=True)


            #edit panel
            cmds.modelEditor(panel, e=True, allObjects=False)
            cmds.modelEditor(panel, e=True, wireframeOnShaded=False)
            cmds.modelEditor(panel, e=True, pluginShapes=True)
            cmds.modelEditor(panel, e=True, nurbsCurves=False)
            cmds.modelEditor(panel, e=True, polymeshes=True)
            cmds.modelEditor(panel, e=True, grid=True)

            
            #edit camera
            try:
                self._editCam(cam_shape, settings_panel)
            except Exception:
                cmds.warning(traceback.format_exc())
            
            
            self.settings_default_maya[panel] = settings_panel
        
        self._getHeadUpDisplay()

    
        return cam_shape
        
    def postPlayblast(self, *args, **kwargs)-> None:
        if kwargs["outputpath"].split(".")[-1] in ["mp4", "mov", "avi", "mkv", "m4v", "webm"]:
            if kwargs["outputpath"].split(".")[-1] != "avi":
                self.outputFile = [kwargs["outputpath"]]
            else:
                self.outputFile = [str(Path(kwargs["outputpath"]).with_suffix(".mp4"))]
            return
        
        folder = os.path.dirname(kwargs["outputpath"])
        filename = os.path.basename(kwargs["outputpath"]).replace("/", "\\")

        # transforme le nom en regex : #### -> (\d+)
        regex = re.escape(filename)
        regex = re.sub(r"(\\#)+", r"(\\d+)", regex)   # gère les '#' échappés
        regex = re.sub(r"%0?\d*d", r"(\\d+)", regex)
        regex = re.compile(f"^{regex}$")

        if not os.path.isdir(folder):
            self.outputFile = []

        matches = [
            os.path.join(folder, f).replace("\\", "/")
            for f in os.listdir(folder)
            if regex.match(f)
        ]
        self.outputFile = sorted(matches)
    
    def postPublish(self, *args, **kwargs) -> None:
        import maya.cmds as cmds #type: ignore
        if self._canStartBurn(kwargs["result"]):
            self._makeBurnIn(self.outputFile)
        else:
            print(f"--> can't burn.  \n out: {self.outputFile}   \n result: {kwargs['result']}")

        for panel in cmds.getPanel(type="modelPanel"):
            if panel not in self.settings_default_maya:
                continue

            cam_shape = cmds.modelEditor(panel, q=True, camera=True)
            cmds.modelEditor(panel, e=True, allObjects=self.settings_default_maya[panel]["allObjects"])
            cmds.modelEditor(panel, e=True, wireframeOnShaded=self.settings_default_maya[panel]["wireframeOnShaded"])
            cmds.modelEditor(panel, e=True, pluginShapes=self.settings_default_maya[panel]["pluginShapes"])
            cmds.modelEditor(panel, e=True, nurbsCurves=self.settings_default_maya[panel]["nurbsCurves"])
            cmds.modelEditor(panel, e=True, polymeshes=self.settings_default_maya[panel]["polymeshes"])
            cmds.modelEditor(panel, e=True, grid=self.settings_default_maya[panel]["grid"])

            try:
                if "overscan" in self.settings_default_maya[panel]:
                    self._setOverscan(cam_shape, self.settings_default_maya[panel]["overscan"])
            except Exception:
                cmds.warning(traceback.format_exc())
        
        self._setHeadUpDisplay()
    

    # --------------------------- hook func ---------------------------
    def _getHeadUpDisplay(self):
        from maya.plugin.evaluator.CacheUiHud import CachePreferenceHud #type: ignore
        import maya.cmds as cmds #type: ignore


        self.settings_header_display["cached"] = CachePreferenceHud().get_value()
        if CachePreferenceHud().get_value():
            cmds.ToggleCacheVisibility()

        for option_var, data_func in _dataOptionVar().items():
            try:
                value = cmds.optionVar(query=option_var)
                self.settings_header_display[option_var] = value
                if value - data_func[1]:
                    data_func[0]()
            
            except Exception as e:
                cmds.warning(e)

    def _setHeadUpDisplay(self):
        from maya.plugin.evaluator.CacheUiHud import CachePreferenceHud #type: ignore
        import maya.cmds as cmds #type: ignore


        if self.settings_header_display["cached"] != CachePreferenceHud().get_value():
            cmds.ToggleCacheVisibility()

        for option_var, data_func in _dataOptionVar().items():
            if option_var not in self.settings_header_display:
                continue

            if self.settings_header_display[option_var] != cmds.optionVar(query=option_var):
                data_func[0]()

    def _editCam(self, cam_shape: str, settings_panel: dict) -> None:
        if cam_shape in self.cam_check:
            return
        
        import maya.cmds as cmds #type: ignore


        # --- store current overscan in a custom attr ---
        settings_panel["overscan"] = cmds.getAttr(cam_shape + ".overscan")
        self._setOverscan(cam_shape, 1.0)
        self.cam_check.append(cam_shape)

    def _setOverscan(self, cam_shape, value):
        import maya.cmds as cmds #type: ignore


        connections = cmds.listConnections(cam_shape + ".overscan", source=True, destination=False, plugs=True) or []
        for src in connections:
            cmds.disconnectAttr(src, cam_shape + ".overscan")

        if cmds.getAttr(cam_shape + ".overscan", lock=True):
            cmds.setAttr(cam_shape + ".overscan", lock=False)
        
        cmds.setAttr(cam_shape + ".overscan", value)


    # --------------------------- creer un brun in ---------------------------
    def _canStartBurn(self, result: list):
        import qtpy.QtWidgets as qt # juste pour le typing
        for res in result:
            if res["state"].__class__.__name__ != "PlayblastClass":
                continue
            
            publish_lay: qt.QHBoxLayout = res["state"].lo_prjMngPublish
            nmb = publish_lay.count()
            check: qt.QCheckBox = publish_lay.itemAt(nmb-1).widget()
            return not check.isChecked()

    
    def _makeBurnIn(self, all_paths: list[str]):
        if not all_paths:
            print("----> no path found", all_paths)
            return all_paths
        
        output_path = all_paths[0]
        input_path = self._renameFile(output_path, False)
        if len(all_paths) > 1:
            input_path = self._frameToPattern(input_path)
            output_path = self._frameToPattern(output_path)

        for p in all_paths:
            self._renameFile(p, True)

        FHAA = self._getArguments()
        burner = burnIn_maya.CreateBurnIn()
        out = burner.burn(input_path=input_path, output_path=output_path, user=FHAA[0],
                    camera=FHAA[1], focal=FHAA[2], department=FHAA[3], task=FHAA[4], start_frame="1001")
    
        return out
    
    def _renameFile(self, path, save):
        p = Path(path)
        new_path = p.with_stem(p.stem + "_old")   # "shot.mp4" -> "shot_burnin.mp4"
        if save:
            os.rename(path, new_path)
        
        return str(new_path)
    
    def _frameToPattern(self, path):
        return re.sub(r"\d+(?=\.\w+$)", lambda m: "%%0%dd" % len(m.group()), path)

    def _getArguments(self):
        import maya.OpenMayaUI as OpenMayaUI #type: ignore
        import maya.OpenMaya as api #type: ignore

        path_scene = self.core.getCurrentFileName()
        entity = self.core.getScenefileData(path_scene)

        view = OpenMayaUI.M3dView.active3dView()
        cam = api.MDagPath()
        view.getCamera(cam)
        camera = cam.fullPathName()
        if "|" in camera:
            camera = camera.split("|")[-1]

        fn_cam = api.MFnCamera(cam)
        focal = fn_cam.focalLength()
        
        return getpass.getuser(), str(camera), str(round(focal, 3))+" mm", entity["department"], entity["task"]



def _dataOptionVar() -> dict:
    import maya.cmds as cmds #type: ignore

    data = {"animationDetailsVisibility": [cmds.ToggleAnimationDetails, 0],
        "cameraNamesVisibility": [cmds.ToggleCameraNames, 0],
        "capsLockVisibility": [cmds.ToggleCapsLockDisplay, 0],
        "currentContainerVisibility": [cmds.ToggleCurrentContainerHud, 0],
        "currentFrameVisibility": [cmds.ToggleCurrentFrame, 0],
        "focalLengthVisibility": [cmds.ToggleFocalLength, 0],
        "frameRateVisibility": [cmds.ToggleFrameRate, 0],
        "hikDetailsVisibility": [cmds.ToggleHikDetails, 0],
        "materialLoadingDetailsVisibility": [cmds.ToggleMaterialLoadingDetailsVisibility, 0],
        "objectDetailsVisibility": [cmds.ToggleObjectDetails, 0],
        "particleCountVisibility": [cmds.ToggleParticleCount, 0],
        "polyCountVisibility": [cmds.TogglePolyCount, 0],
        "sceneTimecodeVisibility": [cmds.ToggleSceneTimecode, 0],
        "selectDetailsVisibility": [cmds.ToggleSelectDetails, 0],
        "symmetryVisibility": [cmds.ToggleSymmetryDisplay, 0],
        "viewAxisVisibility": [cmds.ToggleViewAxis, 0],
        "viewportRendererVisibility": [cmds.ToggleViewportRenderer, 0]}
    
    try:
        data["xgenHUDVisibility"] = [cmds.ToggleXGenDisplayHUD, 0]
    except Exception:
        pass

    return data
