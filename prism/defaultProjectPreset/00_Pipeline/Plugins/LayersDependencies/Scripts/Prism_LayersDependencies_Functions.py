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
from datetime import datetime
import sys
import json

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

        if "Shots" in path_parts:
            shots_idx = path_parts.index("Shots")
            if shots_idx + 2 < len(path_parts):
                seq_name = path_parts[shots_idx + 1]
                shot_folder = path_parts[shots_idx + 2]
                return {
                    "type": "shot",
                    "name": shot_folder,
                    "seq_name": seq_name,
                    "shot_name": shot_folder,
                }
    
    def get_export_type(self, outputpath, dependencies, techstatus_clear_mapping=None):
        outputpath_norm = outputpath.replace("\\", "/")
        keys = set(dependencies.keys()) | set((techstatus_clear_mapping or {}).keys())
        for key in keys:
            if key in outputpath or f"/{key}/" in outputpath_norm:
                return key
        return None
    
    def get_asset_tasks_by_step(self, sg, proj_name, asset_name, step_name, task_names=None, techstatus_filter=None):
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

        filters = [["entity", "is", asset], ["step.Step.short_name", "is", step_name]]
        if task_names:
            filters.append(["content", "in", task_names])
        if techstatus_filter:
            filters.append(["sg_techstatus", "is", techstatus_filter])

        tasks = sg.find(
            "Task",
            filters,
            ["id", "content", "sg_status_list", "step", "sg_techstatus"]
        )
        return tasks
    
    def get_shot_tasks_by_step(self, sg, proj_name, seq_name, shot_name, step_name, task_names=None, techstatus_filter=None):
        project = sg.find_one("Project", [["name", "is", proj_name]], ["id"])
        if not project:
            print(f"Projet '{proj_name}' non trouvé dans ShotGrid.")
            return []
        
        sequence = sg.find_one("Sequence", [["project", "is", project], ["code", "is", seq_name]], ["id"])
        if not sequence:
            print(f"Sequence '{seq_name}' non trouvée dans le projet '{proj_name}'.")
            return []
        
        shot = sg.find_one("Shot", [["project", "is", project], ["sg_sequence", "is", sequence], ["code", "is", shot_name]], ["id"])
        if not shot:
            print(f"Shot '{shot_name}' non trouvé dans le projet '{proj_name}'.")
            return []

        filters = [["entity", "is", shot], ["step.Step.short_name", "is", step_name]]
        if task_names:
            filters.append(["content", "in", task_names])
        if techstatus_filter:
            filters.append(["sg_techstatus", "is", techstatus_filter])

        tasks = sg.find(
            "Task",
            filters,
            ["id", "content", "sg_status_list", "step", "sg_techstatus"]
        )
        return tasks
    
    def build_dependency_comment(self, export_type, artist, date_str, export_comment):
        return f'{export_type} : {artist} ({date_str}) "{export_comment}"'

    def parse_dependency_entry(self, entry):
        """
        Accepte trois formats :
        - str legacy : "LKD"
        - dict simple : {"step": "LKD", "tasks": ["Shading"]}
        - dict avec skip : {"step": "LKD", "tasks": ["Shading"], "skip_if_all_na": true}
        """
        if isinstance(entry, str):
            return entry, None, False
        if isinstance(entry, dict):
            step_name = entry.get("step")
            task_names = entry.get("tasks") or None
            skip_if_all_na = entry.get("skip_if_all_na", False)
            return step_name, task_names, skip_if_all_na
        print(f"Entrée de dépendance non reconnue: {entry!r}")
        return None, None, False

    def get_priority_task(self, tasks):
        """
        Retourne la tâche prioritaire selon la logique :
        - La première tâche sans statut "approved"
        - Ou la dernière tâche si toutes ont "approved"
        """
        if not tasks:
            return None
        
        # Chercher la première tâche sans statut "approved"
        for task in tasks:
            if task.get("sg_status_list") not in ["app", "apr"]:
                return task
        
        # Si toutes les tâches ont "approved", retourner la dernière
        return tasks[-1]
    
    def all_tasks_have_na_status(self, tasks):
        if not tasks:
            return False
        return all(task.get("sg_status_list") == "na" for task in tasks)

    def update_task_status_by_export_type(self, sg, proj_name, entity_info, export_type, dependencies, dependency_comment):
        if export_type not in dependencies:
            return

        if entity_info["type"] == "asset":
            for entry in dependencies[export_type]:
                step_name, task_names, skip_if_all_na = self.parse_dependency_entry(entry)
                if not step_name:
                    continue

                tasks = self.get_asset_tasks_by_step(
                    sg, proj_name, entity_info["name"],
                    step_name=step_name,
                    task_names=task_names
                )
                
                # Check si toutes les tâches sont "na" et skip activé
                if skip_if_all_na and self.all_tasks_have_na_status(tasks):
                    print(f"⊘ Step '{step_name}' : toutes les tasks en 'na', update ignoré")
                    continue
                
                priority_task = self.get_priority_task(tasks)
                if priority_task:
                    sg.update("Task", priority_task["id"], {
                        "sg_techstatus": "toup",
                        "sg_dependency_comment": dependency_comment,
                    })
                    print(f"✓ Task '{priority_task['content']}' ({step_name}) mise à jour avec le statut 'toup'")
            return True

        if entity_info["type"] == "shot":
            for entry in dependencies[export_type]:
                step_name, _, skip_if_all_na = self.parse_dependency_entry(entry)
                if not step_name:
                    continue

                tasks = self.get_shot_tasks_by_step(
                    sg, proj_name,
                    entity_info["seq_name"],
                    entity_info["shot_name"],
                    step_name=step_name
                )
                
                # Check si toutes les tâches sont "na" et skip activé
                if skip_if_all_na and self.all_tasks_have_na_status(tasks):
                    print(f"⊘ Step '{step_name}' : toutes les tasks en 'na', update ignoré")
                    continue
                
                priority_task = self.get_priority_task(tasks)
                if priority_task:
                    sg.update("Task", priority_task["id"], {
                        "sg_techstatus": "toup",
                        "sg_dependency_comment": dependency_comment,
                    })
                    print(f"✓ Task '{priority_task['content']}' ({step_name}) mise à jour avec le statut 'toup'")
            return True

    def clear_techstatus_for_current_step(self, sg, proj_name, entity_info, export_type, techstatus_clear_mapping):
        """
        Regarde sur ShotGrid si la scène exportée a des tasks en techstatus 'toup'
        pour le step correspondant (via techstatus_clear_mapping), et les enlève.
        techstatus_clear_mapping[export_type] peut être :
        - str  : "LGT"                                   -> toutes les tasks du step
        - dict : {"step": "LGT", "tasks": ["Lighting"]}   -> seulement les tasks précisées
        """
        if export_type not in techstatus_clear_mapping:
            return

        step_name, task_names, _ = self.parse_dependency_entry(techstatus_clear_mapping[export_type])
        if not step_name:
            return

        if entity_info["type"] == "asset":
            tasks = self.get_asset_tasks_by_step(
                sg, proj_name, entity_info["name"],
                step_name=step_name,
                task_names=task_names,
                techstatus_filter="toup"
            )
        elif entity_info["type"] == "shot":
            tasks = self.get_shot_tasks_by_step(
                sg, proj_name,
                entity_info["seq_name"],
                entity_info["shot_name"],
                step_name=step_name,
                task_names=task_names,
                techstatus_filter="toup"
            )
        else:
            return

        for task in tasks:
            sg.update("Task", task["id"], {
                "sg_techstatus": "upd",
                "sg_dependency_comment": "",
            })
            print(f"✓ Task '{task['content']}' ({step_name}) : techstatus 'toup' retiré")
    
    def postExport_ShotGrid(self, *args, **kwargs):
        comment = self.core.getStateManager().publishComment
        if comment == 'noHook':
            print('Hook deactivated')
            return

        outputpath = kwargs.get("outputpath", "")
        print('------------------------------------------ out', outputpath)
        if not os.path.exists(outputpath):
            print(f"Le chemin de sortie '{outputpath}' n'existe pas. Vérification des dépendances annulée.")
            return

        with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf-8') as f:
            config = json.load(f)
            dependencies = config.get("dependencies", {})
            techstatus_clear_mapping = config.get("techstatus_clear_mapping", {})
            path_to_project_mapping = config.get("path_to_project_mapping", {})

        export_type = self.get_export_type(outputpath, dependencies, techstatus_clear_mapping)
        if not export_type:
            return
        
        artist = self.core.username
        date_str = datetime.now().strftime("%Y-%m-%d")
        dependency_comment = self.build_dependency_comment(export_type, artist, date_str, comment)

        entity_info = self.extract_entity_info_from_path(outputpath)
        if not entity_info:
            print("Entité non reconnue dans le chemin.")
            return
        print(f"Export {export_type} détecté pour {entity_info['type']}: {entity_info['name']}")

        sg = shotgun_api3.Shotgun(
            SHOTGRID_API_URL,
            script_name=SHOTGRID_SCRIPT_NAME,
            api_key=SHOTGRID_API_KEY
        )

        path_parts = Path(outputpath).parts
        if len(path_parts) > 1:
            proj_name = path_to_project_mapping.get(path_parts[1], path_parts[1])

        # Houdini USD ROP export
        if self.core.appPlugin.pluginName == 'Houdini':
            stateManager = kwargs["state"]
            if stateManager.getRenderNode().type().name() == "usd_rop" or stateManager.getRenderNode().type().name() == "componentoutput":
                self.update_task_status_by_export_type(sg, proj_name, entity_info, export_type, dependencies, dependency_comment)
                self.clear_techstatus_for_current_step(sg, proj_name, entity_info, export_type, techstatus_clear_mapping)

        # Maya export (ABC, USD, or general publish)
        elif self.core.appPlugin.pluginName == 'Maya':
            self.update_task_status_by_export_type(sg, proj_name, entity_info, export_type, dependencies, dependency_comment)
            self.clear_techstatus_for_current_step(sg, proj_name, entity_info, export_type, techstatus_clear_mapping)

        if 'SHOTGRID_ACCESS_TOKEN' in os.environ:
            del os.environ['SHOTGRID_ACCESS_TOKEN']

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True