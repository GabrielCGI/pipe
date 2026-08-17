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
import json
import logging
from pathlib import Path

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

logger = logging.getLogger(__name__)

SETTINGS_ORG = "Prism"
SETTINGS_APP = "VersionsStatusHook"
DATA_JSON_FILE = Path(os.path.dirname(__file__), "configs", "config_not_show_popup.json")
_activeDlg = None

class Prism_VersionsStatusHook_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin

        self.core.registerCallback("postPlayblast", self.postPlayblast, plugin=self)

    @err_catcher(name=__name__)
    def postPlayblast(self, *args, **kwargs):
        global _activeDlg

        scenePath = self.core.getCurrentFileName()
        if not scenePath or not os.path.exists(scenePath):
            logger.warning("Fichier de scène introuvable ('%s'). Fenêtre annulée." % scenePath)
            return

        entity = self.core.getScenefileData(scenePath) #old entity = self.extract_entity_from_scenepath(scenePath)
        
        if not entity:
            logger.warning("Entité non reconnue dans le chemin de la scène ('%s')." % scenePath)
            return

        shotGridplugin = self.core.getPlugin("Shotgrid")
        if not shotGridplugin:
            logger.warning("Plugin Shotgrid introuvable.")
            return
        

        #edit fred: dans un json récupéré des filtre pour s'avoir ou la popup dois ce lancer
        if self._statusDialogisValid(entity):
            try:
                if _activeDlg is not None and _activeDlg.isVisible():
                    _activeDlg.raise_()
                    _activeDlg.activateWindow()
                    return
            except RuntimeError:
                _activeDlg = None

            _activeDlg = PublishTaskStatusDialog(self.core, shotGridplugin, entity)
            _activeDlg.show()

            #edit fred: déplacer la fenêtre plus vers le bas éviter de cacher le popup Prism, ce qui bloque la fenêtre Maya
            decalY = 200
            rect = _activeDlg.geometry()
            _activeDlg.setGeometry(rect.x(), rect.y()+decalY, rect.width(), rect.height())

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True

    #edit fred: dans un json récupéré des filtre pour s'avoir ou la popup dois ce lancer
    def _getDataInJson(self) -> list | None:
        if not os.path.exists(DATA_JSON_FILE):
            return None
        
        with open(DATA_JSON_FILE, "r") as f:
            data = json.loads(f.read())

        if not data:
            return None
        
        return data
    
        
    #edit fred: dans un json récupéré des filtre pour s'avoir ou la popup dois ce lancer
    def _statusDialogisValid(self, entity) -> bool:
        print(entity)
        data_json = self._getDataInJson()
        if data_json is None:
            return True
        
        if entity["department"] in data_json["departments"]:
            return False
        if entity["task"] in data_json["tasks"]:
            return False
        
        if "asset" in entity:
            if entity["asset"] in data_json["assets"]:
                return False
            if entity["asset_path"].split("\\")[0] in data_json["categorys"]:
                return False
        else:
            if entity["shot"] in data_json["shots"]:
                return False
            if entity["sequence"] in data_json["sequences"]:
                return False

        return True


class PublishTaskStatusDialog(QDialog):
    def __init__(self, core, shotGridplugin, entity, parent=None):
        super(PublishTaskStatusDialog, self).__init__()
        self.prjId = shotGridplugin.getCurrentProjectId()
        self.shotGridplugin = shotGridplugin
        self.sg = shotGridplugin.sg
        self.core = core

        #edit fred: récupérer les valeurs courantes de l'entité complète de la scènes
        path_scene = self.core.getCurrentFileName()
        self.entity = self.core.getScenefileData(path_scene)

        self.statuses = [
            "ip",
            "chk",
            "rkdn",
            "rev",
            "q0",
            "app",
        ]

        self.statusLabels = {
            "ip": "WIP",
            "chk": "ToCheck",
            "rkdn": "Retake Done",
            "rev": "WFA",
            "q0": "Q0",
            "app": "App",
        }

        self.sgEntity = self.getSgEntity()
        self.departments = self.getDepartments()
        self.tasksByStep = {}

        self.settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self.lastValues = self.loadLastValues()

        self.core.parentWindow(self, parent=parent)
        self.setupUi()

    @err_catcher(name=__name__)
    def getEntityKey(self):
        """Construit une clé unique identifiant l'entité, utilisée pour stocker/retrouver les derniers paramètres."""
        if self.entity.get("type") == "asset":
            return "asset/%s" % self.entity.get("asset_path")
        elif self.entity.get("type") == "shot":
            return "shot/%s/%s" % (self.entity.get("sequence"), self.entity.get("shot"))
        return None

    @err_catcher(name=__name__)
    def loadLastValues(self):
        """Charge les derniers département/task/statut envoyés pour cette entité, si disponibles."""
        key = self.getEntityKey()
        if not key:
            return {}

        return {
            "department": self.settings.value("%s/department" % key, ""),
            "task": self.settings.value("%s/task" % key, ""),
            "status": self.settings.value("%s/status" % key, ""),
        }

    @err_catcher(name=__name__)
    def saveLastValues(self, stepCode, taskName, status):
        """Sauvegarde le département/task/statut envoyés pour cette entité, pour les réutiliser par défaut."""
        key = self.getEntityKey()
        if not key:
            return

        self.settings.setValue("%s/department" % key, stepCode)
        self.settings.setValue("%s/task" % key, taskName)
        self.settings.setValue("%s/status" % key, status)

    @err_catcher(name=__name__)
    def getSgEntity(self):
        if self.entity.get("type") == "asset":
            entityId = self.shotGridplugin.getAssetId(self.entity, self.prjId)
            if not entityId:
                return None
            return {"type": "Asset", "id": entityId}
        elif self.entity.get("type") == "shot":
            entityId = self.shotGridplugin.getShotId(self.entity, self.prjId)
            if not entityId:
                return None
            return {"type": "Shot", "id": entityId}
        return None

    @err_catcher(name=__name__)
    def getDepartments(self):
        """Récupère les Steps ShotGrid liés au type d'entité (Asset Step / Shot Step)."""
        if not self.sgEntity:
            return []

        entityType = self.sgEntity["type"]
        filters = [["entity_type", "is", entityType]]
        fields = ["code", "short_name"]

        try:
            steps = self.sg.find("Step", filters, fields)
        except Exception as e:
            logger.warning("Erreur lors de la récupération des Steps: %s" % str(e))
            return []

        steps = sorted(steps, key=lambda s: s.get("code") or "")
        return steps

    @err_catcher(name=__name__)
    def getTasksForStep(self, stepCode):
        """Récupère les tasks de l'entité filtrées par Step, avec leur statut courant."""
        if stepCode in self.tasksByStep:
            return self.tasksByStep[stepCode]

        if not self.sgEntity:
            return []

        filters = [
            ["entity", "is", self.sgEntity],
            ["step.Step.code", "is", stepCode],
        ]
        fields = ["content", "sg_status_list"]

        try:
            tasks = self.sg.find("Task", filters, fields)
        except Exception as e:
            logger.warning("Erreur lors de la récupération des Tasks: %s" % str(e))
            tasks = []

        self.tasksByStep[stepCode] = tasks
        return tasks

    @err_catcher(name=__name__)
    def setupUi(self):
        self.lo_main = QVBoxLayout()
        self.setLayout(self.lo_main)
        self.setWindowTitle("Publier un statut de Task")

        entityLabel = self.entity.get("asset_path") or self.core.entities.getShotName(self.entity)
        self.l_description = QLabel("Sélectionnez le département et la task sur lesquels publier un statut :\n(%s)" % entityLabel)
        self.lo_main.addWidget(self.l_description)

        formLayout = QFormLayout()

        shotLabels = []
        if self.core.appPlugin.pluginName == "Houdini" and self.entity['shot'] == '_sequence':
            self.cb_shot = QComboBox()

            shot_path = self.core.getCurrentFileName().split("_sequence")[0]
            shotLabels = [d.name for d in Path(shot_path).iterdir() if d.is_dir() and d.name != '_sequence']

            self.cb_shot.blockSignals(True)
            self.cb_shot.addItems(shotLabels)
            self.cb_shot.blockSignals(False)
            self.cb_shot.currentTextChanged.connect(self.onShotChanged)

            formLayout.addRow("Shot:", self.cb_shot)

        self.cb_department = QComboBox()
        self.cb_department.addItems([s.get("code") for s in self.departments])
        self.cb_department.setDisabled(True) # edit fred rendre par défaut le département nom modifiable
        formLayout.addRow("Département:", self.cb_department)

        self.cb_task = QComboBox()
        formLayout.addRow("Task:", self.cb_task)

        self.cb_status = QComboBox()
        for code in self.statuses:
            self.cb_status.addItem(self.statusLabels.get(code, code), code)
        formLayout.addRow("Statut:", self.cb_status)

        # edit fred: faire un system pour que par défaut il  ai que le département courant qui soit selectionnable 
        # et pas donné la possibiliter aux artiste de choisir le dep
        self.checkbox_all_department = QCheckBox("Choisir département")
        self.checkbox_all_department.clicked.connect(self._activeAllDepartments)
        formLayout.addRow(" ", self.checkbox_all_department)

        self.lo_main.addLayout(formLayout)

        if self.departments:
            deptCodes = [s.get("code") for s in self.departments]
            if self.lastValues.get("department") in deptCodes:
                self.cb_department.setCurrentText(self.lastValues["department"])
            else: #edit fred: prendre par défaut le départements courant de la scene si il n'y a pas de donné save dans la scene
                self.cb_department.setCurrentText(self.entity["department"])
                

        self.cb_department.currentTextChanged.connect(self.onDepartmentChanged)
        self.cb_task.currentTextChanged.connect(self.onTaskChanged)

        if self.departments:
            self.onDepartmentChanged(self.cb_department.currentText())

        self.bb_main = QDialogButtonBox()
        self.b_send = self.bb_main.addButton("Envoyer", QDialogButtonBox.AcceptRole)
        self.bb_main.addButton("Annuler", QDialogButtonBox.RejectRole)
        self.bb_main.accepted.connect(self.onSend)
        self.bb_main.rejected.connect(self.reject)

        self.lo_main.addStretch()
        self.lo_main.addWidget(self.bb_main)

        if not self.departments:
            self.l_description.setText(self.l_description.text() + "\n\nAucun département trouvé pour cette entité.")
            self.b_send.setEnabled(False)

        if shotLabels:
            self.onShotChanged(shotLabels[0])

    @err_catcher(name=__name__)
    def sizeHint(self):
        return QSize(450, 150)

    @err_catcher(name=__name__)
    def setStatusByCode(self, code):
        """Sélectionne dans le combo de statut l'entrée correspondant au code donné."""
        idx = self.cb_status.findData(code)
        if idx >= 0:
            self.cb_status.setCurrentIndex(idx)

    @err_catcher(name=__name__)
    def getCurrentStatusCode(self):
        """Retourne le code du statut actuellement sélectionné (et non le nom affiché)."""
        return self.cb_status.currentData()
    
    @err_catcher(name=__name__)
    def onShotChanged(self, shotName):
        if not shotName:
            return

        self.entity["shot"] = shotName

        entityLabel = self.core.entities.getShotName(self.entity)
        self.l_description.setText(
            "Sélectionnez le département et la task sur lesquels publier un statut :\n(%s)" % entityLabel
        )

        self.tasksByStep = {}
        self.sgEntity = self.getSgEntity()
        self.departments = self.getDepartments()

        self.cb_department.blockSignals(True)
        self.cb_department.clear()
        self.cb_department.addItems([s.get("code") for s in self.departments])
        self.cb_department.blockSignals(False)

        self.lastValues = self.loadLastValues()

        if self.departments:
            deptCodes = [s.get("code") for s in self.departments]
            self.cb_department.blockSignals(True)
            if self.lastValues.get("department") in deptCodes:
                self.cb_department.setCurrentText(self.lastValues["department"])
            self.cb_department.blockSignals(False)
            self.onDepartmentChanged(self.cb_department.currentText())

        self.b_send.setEnabled(bool(self.departments))
        if not self.departments:
            self.core.popup("Aucun département trouvé pour ce shot.")

    @err_catcher(name=__name__)
    def onDepartmentChanged(self, stepCode):
        self.cb_task.blockSignals(True)
        self.cb_task.clear()

        if not stepCode:
            self.cb_task.blockSignals(False)
            return

        tasks = self.getTasksForStep(stepCode)
        taskNames = [t.get("content") for t in tasks]
        self.cb_task.addItems(taskNames)

        if self.lastValues.get("department") == stepCode and self.lastValues.get("task") in taskNames:
            self.cb_task.setCurrentText(self.lastValues["task"])

        self.cb_task.blockSignals(False)

        self.onTaskChanged(self.cb_task.currentText())

    # edit fred: creer la une methode pour passer le comboBox self.cb_department enable
    def _activeAllDepartments(self, check: bool):
        self.cb_department.setDisabled(not check)

    @err_catcher(name=__name__)
    def onTaskChanged(self, taskName):
        if not taskName:
            return

        stepCode = self.cb_department.currentText()
        tasks = self.getTasksForStep(stepCode)
        for task in tasks:
            if task.get("content") == taskName:
                curStatus = task.get("sg_status_list")
                if curStatus in self.statuses:
                    self.setStatusByCode(curStatus)
                break

        if (
            self.lastValues.get("department") == stepCode
            and self.lastValues.get("task") == taskName
            and self.lastValues.get("status") in self.statuses
        ):
            self.setStatusByCode(self.lastValues["status"])

    @err_catcher(name=__name__)
    def onSend(self):
        stepCode = self.cb_department.currentText()
        taskName = self.cb_task.currentText()
        status = self.getCurrentStatusCode()

        if not taskName:
            self.core.popup("Aucune task sélectionnée.")
            return

        tasks = self.getTasksForStep(stepCode)
        taskId = None
        for task in tasks:
            if task.get("content") == taskName:
                taskId = task.get("id")
                break

        if not taskId:
            self.core.popup("Task introuvable.")
            return

        try:
            self.sg.update("Task", taskId, {"sg_status_list": status})
        except Exception as e:
            self.core.popup("Erreur lors de la mise à jour du statut:\n\n%s" % str(e))
            return

        self.saveLastValues(stepCode, taskName, status)

        self.accept()