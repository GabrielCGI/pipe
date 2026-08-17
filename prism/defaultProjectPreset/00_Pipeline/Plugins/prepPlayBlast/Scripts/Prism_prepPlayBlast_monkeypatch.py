from collections import OrderedDict
from importlib import reload
import qtpy.QtWidgets as qt
from pathlib import Path
import getpass
import logging
import glob
import os
import re



import burnIn_maya



reload(burnIn_maya)
logger = logging.getLogger(__name__)



class MonkeyPatchSG(object):
    def __init__(self, core):
        self.core = core

    # add frederic
    def _makeBurnIn(self, all_paths: list[str]):
        if not all_paths:
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


    # ------------------------------ monkeypatch ------------------------------
    def createUploadableMedia(self, paths, parent=None, popup=None):
        self._makeBurnIn(paths) #add frederic 
        mp4Path = self.getExistingUploadableMedia(paths)
        if mp4Path:
            print("publishing existing media: %s" % mp4Path)
            return mp4Path

        if len(paths) > 1:
            inputpath = (
                os.path.splitext(paths[0])[0][: -self.core.framePadding]
                + "%04d".replace("4", str(self.core.framePadding))
                + os.path.splitext(paths[0])[1]
            )
            startNum = os.path.splitext(paths[0])[0][-self.core.framePadding:]
            try:
                startNum = int(startNum)
            except ValueError:
                startNum = 0
        else:
            inputpath = paths[0]
            startNum = 0

        filename = self.core.media.getFilenameWithoutFrameNumber(paths[0])
        filename = os.path.basename(os.path.splitext(filename)[0].strip(".") + ".mp4")
        mp4Path = self.core.getTempFilepath(filename=filename)

        result = self.createUploadableMediaWithMediaConverter(paths, inputpath, startNum, mp4Path)
        if result:
            return result

        self.createUploadableMediaWithFfmpeg(paths, parent, popup, inputpath, startNum, mp4Path)
        return mp4Path

    def getExistingUploadableMedia(self, paths):
        mtype = self.core.mediaProducts.getMediaTypeFromPath(paths[0])
        if mtype == "3drenders":
            versionFolder = os.path.dirname(os.path.dirname(paths[0]))
        else:
            versionFolder = os.path.dirname(paths[0])

        mp4Folder = versionFolder + " (mp4)"
        if os.path.exists(mp4Folder):
            mp4Paths = glob.glob(mp4Folder + "/*.mp4")
            if mp4Paths:
                return mp4Paths[0]

            mp4Paths = glob.glob(mp4Folder + "/**/*.mp4")
            if mp4Paths:
                return mp4Paths[0]

        if paths[0].endswith(".mp4"):
            return paths[0]

        mp4Paths = glob.glob(versionFolder + "/*.mp4")
        if mp4Paths:
            return mp4Paths[0]

        mp4Paths = glob.glob(versionFolder + "/**/*.mp4")
        if mp4Paths:
            return mp4Paths[0]

    def createUploadableMediaWithMediaConverter(self, paths, inputpath, startNum, mp4Path):
        mplug = self.core.getPlugin("MediaExtension")
        if not mplug:
            return

        inExt = os.path.splitext(inputpath)[1]
        ext = os.path.splitext(mp4Path)[1]
        inputspace = "auto"
        if inExt in [".exr", ".hdr", ".dpx"] and mplug.mediaExtension.getSetOcioSpaces():
            inputspace = mplug.mediaExtension.getOcioWorkingSpace()
            if inputspace:
                inputspace = inputspace[0]

        display = mplug.mediaExtension.getDefaultDisplay() or ""
        view = mplug.mediaExtension.getDefaultViewFromDisplay(display) or ""

        presetName = "reviewable"
        preset = mplug.mediaExtension.getConversionPreset(presetName)
        if preset:
            preset["settings"]["outputStartFrame"] = startNum
            preset["settings"]["outputFormat"] = ext
            preset["settings"]["outputPath"] = mp4Path
            print("generating new media using Media Converter and the existing \"%s\" preset" % presetName)
        else:
            preset = {
                "name": "reviewable",
                "category": "",
                "settings": {
                    "autoOutputStartFrame": False,
                    "outputStartFrame": startNum,
                    "outputFormat": ext,
                    "outputPath": mp4Path,
                    "modifiers": [
                        {
                            "type": "colorconversion",
                            "enabled": True,
                            "inputSpace": inputspace,
                            "outputSpace": {
                                "display": display,
                                "view": view,
                            }
                        },
                    ]
                }
            }
            print("generating new media using Media Converter and the default preset")

        result = mplug.convertMediaWithPreset(paths, preset, generateOutputpath=False)
        if result and os.path.exists(mp4Path):
            return mp4Path

    def createUploadableMediaWithFfmpeg(self, paths, parent, popup, inputpath, startNum, mp4Path):
        print("generating new media using ffmpeg")
        conversionSettings = OrderedDict()
        if len(paths) > 1:
            pass
        else:
            conversionSettings["-start_number"] = None
            conversionSettings["-start_number_out"] = None

        conversionSettings["-crf"] = "18"
        if not self.core.media.checkOddResolution(paths[0]):
            conversionSettings["-c"] = "mpeg4"

        text = "Converting media. Please wait..."
        if not popup:
            popup = self.core.waitPopup(self.core, text, parent=parent)
            with popup:
                result = self.core.media.convertMedia(inputpath, startNum, mp4Path, settings=conversionSettings)
        else:
            if popup.msg:
                popup.msg.setText(text)
                qt.QApplication.processEvents()

            result = self.core.media.convertMedia(inputpath, startNum, mp4Path, settings=conversionSettings)

        if not os.path.exists(mp4Path) or os.stat(mp4Path).st_size == 0:
            msg = "Failed to convert media."
            logger.debug("expected outputpath: %s" % mp4Path)
            self.core.ffmpegError("Image conversion", msg, result)
            return
 
