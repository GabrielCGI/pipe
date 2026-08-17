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


from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

import sys
import os
MODULE_PATH = os.path.join(
    os.getenv("ILL_PYTHON_SHARE_PATH"),
    "python311_fastblast_pkgs",
    "Lib",
    "site-packages",
)
if MODULE_PATH not in sys.path:
    sys.path.insert(0, MODULE_PATH)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

SHOTGRID_API_URL = "https://illogic.shotgrid.autodesk.com"
SHOTGRID_SCRIPT_NAME = "outdatedLayers"
SHOTGRID_API_KEY = os.getenv('SHOTGRID_ACCESS_TOKEN')

import shotgun_api3
import shutil
from pathlib import Path


class Prism_Frame2MovieHook_Functions(object):
    def __init__(self, core, plugin):
        print("Frame2MovieHook: Initializing Frame2MovieHook plugin...")
        self.core = core
        self.plugin = plugin
        self.core.registerCallback("onShotGridPublishMedia", self.onShotGridPublishMedia, plugin=self.plugin)

    def onShotGridPublishMedia(self, path_to_frames, path_to_movie, sg_version_id):
        sg = shotgun_api3.Shotgun(
            SHOTGRID_API_URL,
            script_name=SHOTGRID_SCRIPT_NAME,
            api_key=SHOTGRID_API_KEY,
        )

        version = sg.find_one("Version", [["id", "is", sg_version_id]], ["sg_path_to_movie"])
        if version:
            sg.update("Version", sg_version_id, {"sg_path_to_frames": path_to_frames})
            print(f"Updated ShotGrid Version {sg_version_id} with path to frames: {path_to_frames}")
            if path_to_movie[0] != "C":
                sg.update("Version", sg_version_id, {"sg_path_to_movie": path_to_movie})
                print(f"Updated ShotGrid Version {sg_version_id} with path to movie: {path_to_movie}")
            else:
                frames_dir = Path(path_to_frames).parent
                playblast_dir = frames_dir.parent
                new_movie_dir = playblast_dir / (frames_dir.name + " (mp4)")
                if not new_movie_dir.exists():
                    new_movie_dir.mkdir(parents=True)
                    new_movie_path = new_movie_dir / Path(path_to_movie).name
                    shutil.copy2(path_to_movie, new_movie_path)
                sg.update("Version", sg_version_id, {"sg_path_to_movie": str(new_movie_path)})

        if 'SHOTGRID_ACCESS_TOKEN' in os.environ:
            del os.environ['SHOTGRID_ACCESS_TOKEN']
    
    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True
