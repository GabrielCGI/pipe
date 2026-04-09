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
from PrismCore import PrismCore

logger = logging.getLogger(__name__)

DEV_LIST = [
    'FOX-04'
]
ENABLE_DEBUG_MODE = False
DEBUG_MODE = ENABLE_DEBUG_MODE and socket.gethostname() in DEV_LIST
if DEBUG_MODE:
   DEBUG_PATH = "R:/pipeline/networkInstall/python_shares/python311_debug_pkgs/Lib/site-packages"
   if DEBUG_PATH not in sys.path:
       sys.path.insert(0, DEBUG_PATH)
       
   from debug import debug # type: ignore
   
class Prism_KitsuPublishMedia_Functions(object):
    def __init__(self, core: PrismCore, plugin):
        self.core: PrismCore = core
        self.plugin = plugin
        
        # self.initialize()
        self.core.registerCallback("postInitialize", self.initialize, plugin=self)
        
    @err_catcher(name=__name__)
    def initialize(self):
        # do stuff after Prism launched
        self.kitsuplugin = self.core.getPlugin("Kitsu")
        self.prjMng = self.kitsuplugin.prjMng
        self.status = None
        self.taskselected = False
        self.core.plugins.monkeyPatch(self.kitsuplugin.publishMedia, self.publishMedia, self.kitsuplugin, force=True)

    @err_catcher(name=__name__)
    def publishMedia(self, paths, entity, task, version, description="", uploadPreview=True, parent=None, origTask=None, user=None, createTask=False, department=None, playlist=None):
        text = "Publishing media. Please wait..."
        popup = self.kitsuplugin.core.waitPopup(self.kitsuplugin.core, text, parent=parent)
        with popup:
            prjId = self.kitsuplugin.getCurrentProjectId()
            if prjId is None:
                return

            if entity.get("type") == "asset":
                entityName = entity.get("asset_path", "").replace("\\", "/")
                kasset = self.kitsuplugin.getAssetId(entity)
                if not kasset:
                    msg = "The asset \"%s\" doesn't exist in Kitsu. Publish canceled." % entityName
                    self.kitsuplugin.core.popup(msg)
                    return

                ktasks = self.kitsuplugin.makeDbRequest("task", "all_tasks_for_asset", kasset) or []
            elif entity.get("type") == "shot":
                kshot = self.kitsuplugin.getShotByEntity(entity)
                if not kshot:
                    msg = "The shot \"%s\" doesn't exist in Kitsu. Publish canceled." % self.kitsuplugin.core.entities.getShotName(entity)
                    self.kitsuplugin.core.popup(msg)
                    return

                ktasks = self.kitsuplugin.makeDbRequest("task", "all_tasks_for_shot", kshot) or []
                entityName = self.kitsuplugin.core.entities.getShotName(entity)
            else:
                msg = "Invalid entity."
                self.kitsuplugin.core.popup(msg)
                return

            task_found = False
            for ktask in ktasks:
                if self.kitsuplugin.getUseShortTaskNames():
                    taskName = self.kitsuplugin.getTaskTypeNameByTaskTypeId(ktask["task_type_id"])
                else:
                    taskName = ktask["task_type_name"]

                if taskName == task:
                    task_found = True
                    break
            
            if not task_found and createTask and self.kitsuplugin.canCreateTasks:
                department = department or os.getenv("PRISM_KITSU_DFT_MEDIA_PUBLISH_DEPARTMENT", "Compositing")
                ktask = self.kitsuplugin.createTask(entity, department, task)
                if not ktask:
                    return
            elif not self.taskselected or not task_found:
                if self.kitsuplugin.getAllowNonExistentTaskPublishes() and self.kitsuplugin.core.uiAvailable:
                    self.showPublishNonExistentTaskDlg(paths, entity, task, version, description=description, uploadPreview=uploadPreview, parent=parent, mode="media")
                    return
                else:
                    msg = "The task \"%s\" doesn't exist in Kitsu. Publish canceled." % task
                    self.kitsuplugin.core.popup(msg)
                    return

            self.taskselected = False
            tasklabel = origTask or task
            versionName = "%s_%s_%s" % (
                entityName,
                tasklabel,
                version,
            )
            comment = versionName + ":\n\n"
            if self.kitsuplugin.getIncludePathInComments():
                comment += paths[0]
            else:
                comment += os.path.basename(paths[0])

            if description:
                comment += "\n\nDescription: %s" % description

            if self.status:
                statusCode = self.status
            else:
                statusCode = self.kitsuplugin.core.getConfig("prjManagement", "kitsu_versionPubStatus", config="project")
            if statusCode:
                status = self.kitsuplugin.makeDbRequest("task", "get_task_status_by_short_name", statusCode)
            else:
                status = None

            if not status:
                statusname = ktask.get("task_status_name", "")
                statusData = [s for s in self.prjMng.getTaskStatusList() if s["name"].lower() == statusname.lower()]
                if statusData:
                    taskStatusCode = statusData[0]["abbreviation"]
                    status = self.kitsuplugin.makeDbRequest("task", "get_task_status_by_short_name", taskStatusCode)
                else:
                    status = ""

                if not status:
                    msg = "The status \"%s\" doesn't exist in Kitsu. Publish canceled." % statusCode
                    self.kitsuplugin.core.popup(msg)
                    return

            logger.debug("publishing version to Kitsu: %s" % comment)
            try:
                createdComment = self.kitsuplugin.makeDbRequest("task", "add_comment", [ktask, status, comment], allowCache=False)
            except Exception:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                erStr = "ERROR:\n%s" % traceback.format_exc()
                self.kitsuplugin.core.popup(erStr, title="Kitsu Publish")
                return

            if not createdComment or not createdComment.get("id"):
                self.kitsuplugin.core.popup("Failed to create Kitsu comment.\n\nResponse: %s" % createdComment)
                return

            cleanupPreview = True
            if uploadPreview:
                previewPath = self.prjMng.createUploadableMedia(paths, popup=popup)
                cleanupPreview = not os.path.normpath(previewPath).startswith(os.path.normpath(self.core.projectPath))

            else:
                previewPath = self.kitsuplugin.core.getTempFilepath(filename="kitsuMedia.jpg")
                pixmap = QPixmap(10, 10)
                pixmap.fill(Qt.black)
                self.kitsuplugin.core.media.savePixmap(pixmap, previewPath)
                previewPath = self.prjMng.createUploadableMedia([previewPath], popup=popup)

            if previewPath:
                if popup.msg:
                    popup.msg.setText("Uploading media. Please wait...")
                    QApplication.processEvents()

                revision = self.kitsuplugin.core.products.getIntVersionFromVersionName(version)
                self.kitsuplugin.gazu.task.add_preview(ktask, createdComment, previewPath.replace("\\", "/"), revision=revision)
                if cleanupPreview:
                    try:
                        os.remove(previewPath)
                    except Exception:
                        pass

            entity["taskId"] = ktask["id"]
            self.kitsuplugin.getMediaVersions(entity, parent=parent, allowCache=False)
            self.kitsuplugin.getNotes("mediaVersion", entity, allowCache=False)

            if playlist:
                versionData = entity.copy()
                versionData["identifier"] = task
                versionData["version"] = version
                self.prjMng.addMediaToPlaylist(playlist, [versionData])

            url = self.kitsuplugin.makeDbRequest("task", "get_task_url", ktask)
            data = {"url": url, "versionName": versionName}
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
            self.taskselected = True
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
        self.prjMng.dlg_getTaskFromEnity = GetTaskDialog(self.kitsuplugin, tasks, task, parent=parent)
        if mode == "product":
            self.prjMng.dlg_getTaskFromEnity.selected.connect(lambda x: self.prjMng.publishNonExistentProduct(path, entity, x[0], version, description, preview, parent, task))
        else:
            self.prjMng.dlg_getTaskFromEnity.selected.connect(lambda x: onPublish(x))

        self.prjMng.dlg_getTaskFromEnity.show()
        

class GetTaskDialog(QDialog):

    selected = Signal(object)

    def __init__(self, plugin, tasks, current_task, parent=None):
        super(GetTaskDialog, self).__init__()
        self.kitsuplugin = plugin
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
            'wip',
            'wfa',
            "TO CHECK",
            'WFA BLK',
            'WFA SPL',
            'Q0',
            'Q1',
            'QC OK'
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
        if not task or not task.get('status') in self.statuses:
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
