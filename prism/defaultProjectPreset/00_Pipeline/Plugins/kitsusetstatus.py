name = "kitsusetstatus"
classname = "kitsusetstatus"


import os
import sys
import socket
import logging
import traceback
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

logger = logging.getLogger(__name__)

DEV_LIST = [
    # 'FALCON-01',
    # 'FOX-04'
]
ENABLE_DEBUG_MODE = False
DEBUG_MODE = ENABLE_DEBUG_MODE and socket.gethostname() in DEV_LIST
if DEBUG_MODE:
   DEBUG_PATH = "R:/pipeline/networkInstall/python_shares/python311_debug_pkgs/Lib/site-packages"
   if not DEBUG_PATH in sys.path:
       sys.path.insert(0, DEBUG_PATH)
       
   from debug import debug

class kitsusetstatus:
    
    def __init__(self, core):
        self.core = core
        self.version = "v1.0.0"

        self.core.registerCallback("postInitialize", self.postInitialize, plugin=self)


    def postInitialize(self):
        # do stuff after Prism launched
        self.kitsuplugin = self.core.getPlugin("Kitsu")
        self.prjMng = self.kitsuplugin.prjMng
        self.status = None
        self.taskselected = False
        self.core.plugins.monkeyPatch(self.kitsuplugin.publishMedia, self.publishMedia, self.kitsuplugin, force=True)


    @err_catcher(name=__name__)
    def publishMedia(self, paths, entity, task, version, description="", uploadPreview=True, parent=None, origTask=None):
        if DEBUG_MODE:
            debug.debug()
            debug.debugpy.breakpoint()
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

                ktasks = self.kitsuplugin.makeDbRequest("task", "all_tasks_for_asset", kasset)

            elif entity.get("type") == "shot":
                kshot = self.kitsuplugin.getShotByEntity(entity)
                if not kshot:
                    msg = "The shot \"%s\" doesn't exist in Kitsu. Publish canceled." % self.kitsuplugin.core.entities.getShotName(entity)
                    self.kitsuplugin.core.popup(msg)
                    return

                ktasks = self.kitsuplugin.makeDbRequest("task", "all_tasks_for_shot", kshot)
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

            if not self.taskselected or not task_found: 
                if self.kitsuplugin.getAllowNonExistentTaskPublishes():
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
                if len(paths) == 1 and os.path.splitext(paths[0])[1] in [".mp4", ".jpg", ".png"]:
                    previewPath = paths[0]
                    cleanupPreview = False
                else:
                    previewPath = self.prjMng.createUploadableMedia(paths, popup=popup)

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
                self.kitsuplugin.gazu.task.add_preview(ktask, createdComment, previewPath, revision=revision)
                if cleanupPreview:
                    try:
                        os.remove(previewPath)
                    except Exception:
                        pass

            entity["taskId"] = ktask["id"]
            self.kitsuplugin.getMediaVersions(entity, parent=parent, allowCache=False)
            self.kitsuplugin.getNotes("mediaVersion", entity, allowCache=False)

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
            self.taskselected = True
            self.prjMng.publishNonExistentMedia(path, entity, selectedTask, version, description, uploadPreview, parent, task)

        self.prjMng.dlg_getTaskFromEnity = GetTaskDialog(self.kitsuplugin, tasks, parent=parent)
        if mode == "product":
            self.prjMng.dlg_getTaskFromEnity.selected.connect(lambda x: self.prjMng.publishNonExistentProduct(path, entity, x[0], version, description, preview, parent, task))
        else:
            self.prjMng.dlg_getTaskFromEnity.selected.connect(lambda x: onPublish(x))

        self.prjMng.dlg_getTaskFromEnity.show()
        

class GetTaskDialog(QDialog):

    selected = Signal(object)

    def __init__(self, plugin, tasks, parent=None):
        super(GetTaskDialog, self).__init__()
        self.kitsuplugin = plugin
        self.prjMng = plugin.prjMng
        self.core = self.prjMng.core
        self.tasks = tasks or []
        self.statusList = self.prjMng.getTaskStatusList()
        self.statuses = [
            'wip',
            'wfa',
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
        self.cb_tasks.addItems([t["task"] for t in self.tasks])
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
                # for status in self.statusList:
                #     if status.get('abbreviation') == task['status']:
                #         return status

    @err_catcher(name=__name__)
    def onAccepted(self):
        task = self.cb_tasks.currentText()
        status = self.cb_status.currentText()
        # statusData = [s for s in self.statusList if s["abbreviation"].lower() == statusname.lower()]
        # if statusData:
        #     status = statusData
        # else:
        #     status = None
        kitsu_infos = (task, status)
        self.hide()
        self.selected.emit(kitsu_infos)
        self.accept()