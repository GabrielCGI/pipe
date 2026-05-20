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


import os
import shotgun_api3
from pathlib import Path
import sys
import json

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

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


class Prism_LayersDependencies_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin

        self.core.registerCallback("postExport", self.postExport_ShotGrid, plugin=self)
    
    def extract_entity_info_from_path(self, outputpath):
        path_parts = Path(outputpath).parts
        if "Assets" in path_parts:
            assets_idx = path_parts.index("Assets")
            if assets_idx + 2 < len(path_parts):
                asset_type = path_parts[assets_idx + 1]
                asset_name = path_parts[assets_idx + 2]
                return {"type": "asset", "name": asset_name, "asset_type": asset_type}
    
    def get_export_type(self, outputpath, dependencies):
        outputpath_norm = outputpath.replace("\\", "/")
        for key in dependencies.keys():
            if key in outputpath or f"/{key}/" in outputpath_norm:
                return key
        return None
    
    def get_asset_tasks_by_step(self, sg, proj_name, asset_name, step_name):
        project = sg.find_one("Project", [["name", "is", proj_name]], ["id"])
        if not project:
            print(f"Projet '{proj_name}' non trouvé dans ShotGrid.")
            return []
        
        assets = sg.find(
            "Asset",
            [["project", "is", project], ["code", "is", asset_name]],
            ["id"]
        )
        if not assets:
            print(f"Asset '{asset_name}' non trouvé dans le projet '{proj_name}'.")
            return []
        
        asset = assets[0]
        
        tasks = sg.find(
            "Task",
            [["entity", "is", asset], ["step.Step.short_name", "is", step_name]],
            ["id", "content", "sg_status_list", "step"]
        )
        return tasks
    
    def update_task_status_by_export_type(self, sg, proj_name, entity_info, export_type, dependencies):
        if entity_info["type"] == "asset" and export_type in dependencies:
            for step_name in dependencies[export_type]:
                tasks = self.get_asset_tasks_by_step(sg, proj_name, entity_info["name"], step_name=step_name)
                for task in tasks:
                    sg.update("Task", task["id"], {"sg_techstatus": "toup"})
                    print(f"✓ Task '{task['content']}' ({step_name}) mise à jour avec le statut 'toup'")
            return True
    
    def postExport_ShotGrid(self, *args, **kwargs):
        comment = self.core.getStateManager().publishComment
        if comment == 'noHook':
            print('Hook deactivated')
            return

        if self.core.appPlugin.pluginName == 'Houdini':
            stateManager = kwargs["state"]

            if stateManager.getRenderNode().type().name() == "usd_rop":
                outputpath = kwargs.get("outputpath", "")
                if not os.path.exists(outputpath):
                    print(f"Le chemin de sortie '{outputpath}' n'existe pas. Vérification des dépendances annulée.")
                    return

                with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    dependencies = config.get("dependencies", {})
                    path_to_project_mapping = config.get("path_to_project_mapping", {})

                export_type = self.get_export_type(outputpath, dependencies)
                if not export_type:
                    return

                entity_info = self.extract_entity_info_from_path(outputpath)

                print(f"Export {export_type} détecté pour {entity_info['type']}: {entity_info['name']}")

                sg = shotgun_api3.Shotgun(
                    SHOTGRID_API_URL,
                    script_name=SHOTGRID_SCRIPT_NAME,
                    api_key=SHOTGRID_API_KEY
                )

                path_parts = Path(outputpath).parts
                if len(path_parts) > 1:
                    proj_name = path_to_project_mapping.get(path_parts[1], path_parts[1])

                self.update_task_status_by_export_type(sg, proj_name, entity_info, export_type, dependencies)

            if 'SHOTGRID_ACCESS_TOKEN' in os.environ:
                del os.environ['SHOTGRID_ACCESS_TOKEN']

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True
