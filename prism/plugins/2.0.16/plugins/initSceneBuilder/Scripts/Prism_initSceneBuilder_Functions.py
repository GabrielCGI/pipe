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


from PrismUtils.Decorators import err_catcher_plugin as err_catcher #type: ignore
import qtpy.QtWidgets  as qt
import qtpy.QtCore   as qtc
from pathlib import Path
import importlib
import socket
import json
import sys
import os



MACHINE_DEBUG   = ["FALCON-01", "FOX-04"]
HOSTNAME = socket.gethostname()
DEV_MODE = False
W_CTYPES = 1
DEBUG = 0

SHOTBUIDLER_INIT = True



if DEV_MODE and HOSTNAME in MACHINE_DEBUG:
    sys.path.append("R:/pipeline/pipe_public/develop/prism-scene-builder")
else:
    sys.path.append("R:/pipeline/pipe_public/prism-scene-builder")



# ------------------------------window mode------------------------------
if DEV_MODE and HOSTNAME in MACHINE_DEBUG :
    if W_CTYPES:
        import ctypes
        ctypes.windll.kernel32.AllocConsole()
        sys.stdout = open('CONOUT$', 'w')
        sys.stderr = open('CONOUT$', 'w')
        sys.stdin = open('CONIN$', 'r')
        os.system("cls")
else:
    W_CTYPES = 0
    DEBUG = 0

# ------------------------------window mode------------------------------



try:
    import sceneBuilder #type: ignore
except Exception as e:
    SHOTBUIDLER_INIT = False
    print(e)
    pass


class Prism_initSceneBuilder_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.core.registerCallback("onSceneFromPresetCreated", self.SceneCreate, plugin=self)

    @err_catcher(name=__name__)
    def SceneCreate(self, entityPrism, path):
        dcc = self.detectSoftware(path)
        if not dcc:
            self.core.popup("no type of dcc found\nsceneBuilder not exectuted", severity="info")
            return


        yaml_path, routine_path = self.getPath()
        if SHOTBUIDLER_INIT:
            modifiers = qt.QApplication.keyboardModifiers()

            importlib.reload(sceneBuilder)
            if modifiers & qtc.Qt.ControlModifier:
                shotbuild = sceneBuilder.sceneBuilder(entityPrism, yaml_path, routine_path, W_CTYPES, DEBUG)
                shotbuild.main(path, dcc, True)
        else:
            self.core.popup("sceneBuilder not init")

    
    def getPath(self):
        project_path = self.core.projectPath

        yaml_path       = project_path + "/00_Pipeline/CustomModules/Python/sceneBuilder/routine/builderCore_routine.yaml"
        templates_path  = project_path + "/00_Pipeline/CustomModules/Python/sceneBuilder/templates"

        return yaml_path, templates_path

    def detectSoftware(self, path):
        path_soft = None
        path_pyth = None
        name_dcc = None
        execution = ""
        if path.endswith(".ma") or path.endswith(".mb"):
            name_dcc = "MAYA"
            execution = "mayapy.exe"

        elif path.endswith(".hip") or path.endswith(".hipnc"):
            name_dcc = "HOUDINI"
            execution = "hython.exe"
        else:
            return None

        # elif path.endswith(".nk"):
        #     name_dcc = "NUKE"
        #     execution = "nuke.exe"


        path_soft = self.findPathSoft(name_dcc)
        path_pyth = str(Path(path_soft).parent) + "\\" + execution

        return {"name": name_dcc, "pathSoft": path_soft, "pathPy": path_pyth}

    def findPathSoft(self, dcc):
        if not dcc:
            return None

        project = self.core.projectPath
        with open(f"{project}00_Pipeline/Configs/launcher.json", "r") as f:
            data_launcher = json.loads(f.read())

        path = None
        for app in data_launcher["apps"]:
            if app["label"].upper() != dcc:
                continue

            for version in app["versions"]:
                if not "preferred" in version:
                    continue

                if not version["preferred"]:
                    continue

                path = version["cmd"]
                break

            if path:
                break

        return path
    
    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True

