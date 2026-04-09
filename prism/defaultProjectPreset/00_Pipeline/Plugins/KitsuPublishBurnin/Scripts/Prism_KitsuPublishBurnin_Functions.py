# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2023 Richard Frangenberg
# Copyright (C) 2023 Prism Software GmbH
#
# Licensed under GNU LGPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.

import logging
import glob
import os
from collections import OrderedDict

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher
from PrismCore import PrismCore

logger = logging.getLogger(__name__)

class Prism_KitsuPublishBurnin_Functions(object):
    def __init__(self, core: PrismCore, plugin):
        self.core: PrismCore = core
        self.plugin = plugin
        self.version = "v1.0.2"

        prjplug = self.core.getPlugin("ProjectManagement")
        if prjplug:
            self.core.plugins.monkeyPatch(prjplug.createUploadableMedia, self.createUploadableMedia, plugin, force=True)

    def createUploadableMedia(self, paths, parent=None, popup=None):
        mp4Path = self.getExistingUploadableMedia(paths)
        print("existing:", mp4Path)
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
                QApplication.processEvents()

            result = self.core.media.convertMedia(inputpath, startNum, mp4Path, settings=conversionSettings)

        if not os.path.exists(mp4Path) or os.stat(mp4Path).st_size == 0:
            msg = "Failed to convert media."
            logger.debug("expected outputpath: %s" % mp4Path)
            self.core.ffmpegError("Image conversion", msg, result)
            return
 

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True
