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
import sys
import shutil
import socket
import logging
import traceback
from pathlib import Path

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher
import edit_data_scene_to_shotGrid as editData # Illigic add settings and import 
from PrismCore import PrismCore

logger = logging.getLogger(__name__)

DEV_LIST = [
    'FOX-04',
    'SPRINTER-03',
    "FALCON-01"
]
ENABLE_DEBUG_MODE = False
if ENABLE_DEBUG_MODE and socket.gethostname() in DEV_LIST:
   DEBUG_PATH = "R:/pipeline/networkInstall/python_shares/python311_debug_pkgs/Lib/site-packages"
   if DEBUG_PATH not in sys.path:
       sys.path.insert(0, DEBUG_PATH)
       
   from debug import debug # type: ignore
   
class Prism_shotGridPublishMedia_Functions(object):
    def __init__(self, core: PrismCore, plugin):
        self.core: PrismCore = core
        self.plugin = plugin
        self.status = None
        self.initialize()
        self.core.registerCallback("postInitialize", self.initialize, plugin=self)
        
    @err_catcher(name=__name__)
    def initialize(self):
        # do stuff after Prism launched
        self.shotGridplugin = self.core.getPlugin("Shotgrid")
        self.prjMng = self.shotGridplugin.prjMng

        self.core.plugins.monkeyPatch(self.shotGridplugin.publishMedia, self.publishMedia, self.shotGridplugin, force=True)
    
    @err_catcher(name=__name__)
    def getTaskId(self, entity, prjId, taskname):
        fields = []

        filters = [
            ["project", "is", {"type": "Project", "id": prjId}],
            ["content", "is", taskname],
            # Edit par Illogic avant : ["tags", "name_not_contains", "noPrism"],
        ]
        if entity.get("type") == "asset":
            assetPath = entity.get("asset_path", "").replace("\\", "/")
            if "/" in assetPath:
                assetPathData = assetPath.split("/")
                assetCat = assetPathData[0]
                assetName = assetPathData[1]
            else:
                assetName = assetPath
                assetCat = ""

            filters += [
                ["entity.Asset.code", "is", assetName],
                ["entity.Asset.sg_asset_type", "is", assetCat],
            ]
        elif entity.get("type") == "shot":
            shotName = entity.get("shot")
            sequenceName = entity.get("sequence")
            filters += [
                ["entity.Shot.code", "is", shotName],
            ]
            useEpisodes = self.core.getConfig(
                "globals",
                "useEpisodes",
                config="project",
            ) or False
            if useEpisodes:
                episodeName = entity.get("episode")
                filters.append(["entity.Shot.sg_sequence.Sequence.code", "is", sequenceName])
                filters.append(["entity.Shot.sg_sequence.Sequence.episode.Episode.code", "is", episodeName])
            else:
                if self.shotGridplugin.episodeSeparator in sequenceName:
                    episodeName, sequenceName = sequenceName.split(self.shotGridplugin.episodeSeparator)
                    filters.append(["entity.Shot.sg_sequence.Sequence.code", "is", sequenceName])
                    filters.append(["entity.Shot.sg_sequence.Sequence.episode.Episode.code", "is", episodeName])
                else:
                    filters.append(["entity.Shot.sg_sequence.Sequence.code", "is", sequenceName])

        tasks = self.shotGridplugin.makeDbRequest("find", ["Task", filters, fields])
        if tasks:
            return tasks[0]["id"]

    @err_catcher(name=__name__)
    def publishMedia(self, paths, entity, task, version, description="", uploadPreview=True, parent=None, origTask=None, user=None, createTask=False, department=None, playlist=None):
        if ENABLE_DEBUG_MODE and socket.gethostname() in DEV_LIST:
            debug.debug()
            debug.debugpy.breakpoint()
        
        text = "Publishing media. Please wait..."
        popup = self.core.waitPopup(self.core, text, parent=parent)
        with popup:
            prjId = self.shotGridplugin.getCurrentProjectId()
            if prjId is None:
                return

            if entity.get("type") == "asset":
                curEntityId = self.shotGridplugin.getAssetId(entity, prjId)
                if not curEntityId:
                    msg = "Invalid asset."
                    self.core.popup(msg)
                    return

                entityName = entity.get("asset_path", "").replace("\\", "/").replace("/", "_")
                sgEntity = {"type": "Asset", "id": curEntityId}
            elif entity.get("type") == "shot":
                curEntityId = self.shotGridplugin.getShotId(entity, prjId)
                if not curEntityId:
                    msg = "Invalid shot."
                    self.core.popup(msg)
                    return

                entityName = self.core.entities.getShotName(entity)
                sgEntity = {"type": "Shot", "id": curEntityId}
            else:
                msg = "Invalid entity."
                self.core.popup(msg)
                return

            curTaskId = self.getTaskId(entity, prjId, task)
            if not curTaskId:
                if createTask and self.shotGridplugin.canCreateTasks:
                    department = department or os.getenv("PRISM_SG_DFT_MEDIA_PUBLISH_DEPARTMENT", "Comp")
                    curTask = self.createTask(entity, department, task)
                    if not curTask:
                        return

                    curTaskId = curTask["id"]
                else:
                    if self.shotGridplugin.getAllowNonExistentTaskPublishes() and self.core.uiAvailable:
                        # Illogic Custom: Change publish task pop up to add identifier and status selection
                        self.showPublishNonExistentTaskDlg(paths, entity, task, version, description=description, uploadPreview=uploadPreview, parent=parent, mode="media")
                        return
                    else:
                        msg = "Task \"%s\" doesn't exist in Shotgrid." % task
                        self.core.popup(msg)
                        return

            framePath = paths[0]
            base, ext = os.path.splitext(framePath)
            baseData = base.rsplit(".", 1)
            if len(baseData) == 2:
                if len(baseData[1]) == self.core.framePadding:
                    try:
                        int(baseData[1])
                        framePath = baseData[0] + "." + "#" * self.core.framePadding + ext
                    except Exception:
                        pass

            taskname = origTask or task
            versionName = "%s_%s_%s" % (
                entityName,
                taskname,
                version,
            )
            if self.shotGridplugin.publishVersionNameFromFilename:
                descrSuffix = "\n<prism>" + versionName
                versionName = os.path.splitext(os.path.basename(framePath))[0].replace("." + "#" * self.core.framePadding, "")
            else:
                descrSuffix = ""

            comment = versionName
            comment += "\nPath: %s" % framePath
            if description:
                comment += "\nDescription: %s" % description

            logger.debug("publishing version to Shotgrid: %s" % comment)
            data = {
                "project": {"type": "Project", "id": prjId},
                "code": versionName,
                "description": description + descrSuffix,
                "sg_path_to_frames": framePath,
                "entity": sgEntity,
                "sg_task": {"type": "Task", "id": curTaskId},
            }
            startNum = None
            if len(paths) > 1:
                startNum = os.path.splitext(paths[0])[0][-self.core.framePadding:]
            else:
                mtype = self.core.mediaProducts.getMediaTypeFromPath(paths[0])
                versionData = self.core.paths.getMediaProductData(paths[0], mediaType=mtype)
                if "startframe" in versionData:
                    startNum = versionData["startframe"]

            if startNum is None and entity.get("type") == "shot":
                shotRange = self.core.entities.getShotRange(entity)
                if shotRange:
                    startNum = shotRange[0]

            if startNum is not None:
                try:
                    data["sg_first_frame"] = int(startNum)
                except:
                    pass
            
            # Illogic Custom: Récupère le statut mis sur l'interface utilisateur et ajouter un path to geometry
            data = editData.mainCustom(data, self.core)
            

            user = user or os.getenv("PRISM_SG_USERNAME")
            if user:
                data["user"] = self.shotGridplugin.getUserByName(user)

            try:
                createdVersion = self.shotGridplugin.sg.create("Version", data)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                erStr = "ERROR:\n%s" % traceback.format_exc()
                self.core.popup(erStr, title="Shotgrid Publish")
                return

            if uploadPreview:
                cleanPreview = True
                if len(paths) == 1 and os.path.splitext(paths[0])[1] in [".mp4", ".jpg", ".png", ".avi", ".mov"]:
                    previewPath = paths[0]
                    cleanPreview = False
                else:
                    previewPath = self.prjMng.createUploadableMedia(paths, popup=popup)

                if previewPath:
                    if popup.msg:
                        popup.msg.setText("Uploading media. Please wait...")
                        QApplication.processEvents()

                    try:
                        self.shotGridplugin.sg.upload(
                            "Version",
                            createdVersion["id"],
                            previewPath,
                            "sg_uploaded_movie",
                        )
                    except Exception as e:
                        msg = "Uploading proxy video failed:\n\n%s" % str(e)
                        self.core.popup(msg)

                    if cleanPreview:
                        try:
                            os.remove(previewPath)
                        except Exception:
                            pass

            if createdVersion and createdVersion.get("id"):
                self.shotGridplugin.getMediaVersions(entity, parent=parent, allowCache=False)

            sgSite = self.shotGridplugin.sg.base_url
            sgSite += "/detail/Version/" + str(createdVersion["id"])
            data = {"url": sgSite, "versionName": versionName}
            return data

    @err_catcher(name=__name__)
    def showPublishNonExistentTaskDlg(self, path, entity, task, version, description="", uploadPreview=True, preview=None, parent=None, mode=None):
        tasks = self.prjMng.curManager.getTasksFromEntity(entity)
        if not tasks:
            self.prjMng.core.popup("The selected entity has no tasks in %s. Unable to publish %s." % (self.prjMng.curManager.name, mode))
            return
        
        def onPublish(kitsu_infos):
            selectedTask, selectedStatus = kitsu_infos
            self.status = selectedStatus
            replace_version = version
            # ------------------------------ déplacer et mettre la version exportée de Kitsu à l'endroit du publish ------------------------------
            src = Path(path[0]) #exemple: I:\\McDonald_2511\\03_Production\\Shots\\SHOT-TEST\\fred\\Playblasts\\Anim\\v006\\SHOT-TEST-fred_Anim_v006.mp4
            start_new_path = src.parent.parent.parent.__str__() + "\\" + selectedTask
            file = src.parts[-1].__str__()
            version_media = src.parts[-2].__str__()
            task_media = src.parts[-3].__str__()
            if selectedTask != task_media: # permet de voir si on publie dans la même tâche entre Kitsu et Prism pour éviter de réécrire une version en plus dans le même identifiant
                new_version = None
                if os.path.exists(start_new_path):
                    new_version = sorted(os.listdir(start_new_path))
                else:
                    os.makedirs(start_new_path)
                
                if new_version:
                    new_version = "v"  + str(int(new_version[-1][1:]) + 1).zfill(3)
                else:
                    new_version = "v001"

                os.makedirs(f"{start_new_path}\\{new_version}")
                new_file = file.replace(version_media, new_version).replace(task_media, selectedTask)
                dst = f"{start_new_path}\\{new_version}\\{new_file}"
                shutil.copy2(src, dst)

                #ramplacer les variable du début par mes variables
                replace_version = new_version
                path[0] = dst
                print("src:", src)
                print("dst:", dst)
            # ------------------------------ déplacer et mettre la version exportée de Kitsu à l'endroit du publish ------------------------------
            self.prjMng.publishNonExistentMedia(path, entity, selectedTask, replace_version, description, uploadPreview, parent, task)
        
        self.prjMng.dlg_getTaskFromEnity = GetTaskDialog(self.shotGridplugin, tasks, task, parent=parent)
        if mode == "product":
            self.prjMng.dlg_getTaskFromEnity.selected.connect(lambda x: self.prjMng.publishNonExistentProduct(path, entity, x[0], version, description, preview, parent, task))
        else:
            self.prjMng.dlg_getTaskFromEnity.selected.connect(lambda x: onPublish(x))

        self.prjMng.dlg_getTaskFromEnity.show()
        



class GetTaskDialog(QDialog):
    selected = Signal(object)
    
    def __init__(self, plugin, tasks, current_task, parent=None):
        super(GetTaskDialog, self).__init__()
        self.shotGridplugin = plugin
        self.prjMng = plugin.prjMng
        self.core = self.prjMng.core
        self.tasks = tasks or []
        self.tasks_names = [t["task"] for t in self.tasks]
        if current_task in self.tasks_names:
            self.current_task = current_task
        elif len(tasks):
            self.current_task = tasks[0]["task"]
        else:
            self.current_task = ""
        self.statusList = self.prjMng.getTaskStatusList()
        self.statuses = [
            'rev',
            'na' ,
            "bug",
            'q0' ,
            'app'
        ]
        self.core.parentWindow(self, parent=parent)
        self.setupUi()

    @err_catcher(name=__name__)
    def setupUi(self):
        self.lo_main = QVBoxLayout()
        self.setLayout(self.lo_main)
        self.setWindowTitle("Select Task")
        self.l_description = QLabel("Select the %s task to which you want to publish:" % self.prjMng.curManager.name)
        self.cb_tasks = QComboBox()
        self.cb_tasks.addItems(self.tasks_names)
        self.cb_tasks.setCurrentText(self.current_task)
        self.cb_status = QComboBox()
        self.cb_status.addItems(self.statuses)
        self.onTaskChanged(None)
        self.cb_tasks.currentTextChanged.connect(self.onTaskChanged)

        self.lo_main.addWidget(self.l_description)
        self.lo_main.addWidget(self.cb_tasks)
        self.lo_main.addWidget(self.cb_status)

        self.bb_main = QDialogButtonBox()
        self.bb_main.addButton("Publish", QDialogButtonBox.AcceptRole)
        self.bb_main.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.bb_main.accepted.connect(self.onAccepted)
        self.bb_main.rejected.connect(self.reject)
        self.lo_main.addStretch()
        self.lo_main.addWidget(self.bb_main)

    @err_catcher(name=__name__)
    def sizeHint(self):
        return QSize(450, 120)
    
    @err_catcher(name=__name__)
    def onTaskChanged(self, text):
        taskname = self.cb_tasks.currentText()
        task = self.getTaskStatus(taskname)
        if not task or task.get('status') not in self.statuses:
            self.cb_status.setCurrentText('wfa')
            return
        self.cb_status.setCurrentText(task.get('status'))
        
    def getTaskStatus(self, taskname):
        for task in self.tasks:
            if task.get('task') == taskname:
                return task

    @err_catcher(name=__name__)
    def onAccepted(self):
        task = self.cb_tasks.currentText()
        status = self.cb_status.currentText()
        kitsu_infos = (task, status)
        self.hide()
        self.selected.emit(kitsu_infos)
        self.accept()

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True
