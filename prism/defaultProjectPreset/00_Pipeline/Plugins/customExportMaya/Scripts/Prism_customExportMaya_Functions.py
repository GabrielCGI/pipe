# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com-
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
import platform
import logging



from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from importlib import reload
import hook_preExport_Illogic as hookPreExport

from PrismUtils.Decorators import err_catcher as err_catcher



logger = logging.getLogger(__name__)



class Prism_customExportMaya_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        if self.core.appPlugin.pluginName == 'Maya':
            self.core.plugins.monkeyPatch(self.core.appPlugin.sm_export_exportAppObjects, self.sm_export_exportAppObjects, self.plugin)

    @err_catcher(name=__name__)
    def startup(self, origin):
        import maya.mel as mel
        import maya.cmds as cmds
        import maya.OpenMaya as api

        if self.core.uiAvailable:
            if QApplication.instance() is None:
                return False

            if not hasattr(QApplication, "topLevelWidgets"):
                return False

            for obj in QApplication.topLevelWidgets():
                if obj.objectName() == "MayaWindow":
                    mayaQtParent = obj
                    break
            else:
                return False

            try:
                topLevelShelf = mel.eval("string $m = $gShelfTopLevel")
            except:
                return False

            if not topLevelShelf:
                return False

            if (
                cmds.shelfTabLayout(topLevelShelf, query=True, tabLabelIndex=True)
                is None
            ):
                return False

            origin.timer.stop()

            if platform.system() == "Darwin":
                origin.messageParent = QWidget()
                origin.messageParent.setParent(mayaQtParent, Qt.Window)
                if self.core.useOnTop:
                    origin.messageParent.setWindowFlags(
                        origin.messageParent.windowFlags() ^ Qt.WindowStaysOnTopHint
                    )
            else:
                origin.messageParent = mayaQtParent

            self.addMenu()
            origin.startAutosaveTimer()
        else:
            origin.messageParent = QWidget()

        cmds.loadPlugin("AbcExport.mll", quiet=True)
        cmds.loadPlugin("AbcImport.mll", quiet=True)
        try:
            cmds.loadPlugin("fbxmaya.mll", quiet=True)
        except Exception as e:
            logger.warning("failed to load fbxmaya.mll: %s" % str(e))

        api.MSceneMessage.addCallback(api.MSceneMessage.kAfterOpen, origin.sceneOpen)

    @err_catcher(name=__name__)
    def addMenu(self):
        import maya.cmds as cmds
        import maya.mel as mel

        if cmds.about(batch=True):
            return

        # destroy any pre-existing shotgun menu - the one that holds the apps
        if cmds.menu("PrismMenu", exists=True):
            cmds.deleteUI("PrismMenu")

        # create a new shotgun disabled menu if one doesn't exist already.
        if not cmds.menu("PrismMenu", exists=True):
            prism_menu = cmds.menu(
                "PrismMenu",
                label="Prism",
                parent=mel.eval("$retvalue = $gMainWindow;"),
            )
            cmds.menuItem(
                label="Save Version",
                annotation="Saves the current file to a new version",
                parent=prism_menu,
                command=lambda x: self.core.saveScene(),
            )
            cmds.menuItem(
                label="Save Comment...",
                annotation="Saves the current file to a new version with a comment",
                parent=prism_menu,
                command=lambda x: self.core.saveWithComment(),
            )
            cmds.menuItem(
                label="Project Browser...",
                annotation="Opens the Project Browser",
                parent=prism_menu,
                command=lambda x: self.core.projectBrowser(),
            )
            cmds.menuItem(
                label="State Manager...",
                annotation="Opens the State Manager",
                parent=prism_menu,
                command=lambda x: self.core.stateManager(),
            )
            cmds.menuItem(
                label="Settings...",
                annotation="Opens the Prism Settings",
                parent=prism_menu,
                command=lambda x: self.core.prismSettings(),
            )
            self.core.callback(name="onMayaMenuCreated", args=[self, prism_menu])

    @err_catcher(name=__name__)
    def onShelfClickedImport(self, doubleclick=False):
        if doubleclick:
            self.onShelfClickedImportConnectedAssets()
            return

        sm = self.core.getStateManager()
        if not sm:
            return

        state = sm.createState(
            "ImportFile",
            setActive=True,
            openProductsBrowser=True,
        )

        return state

    @err_catcher(name=__name__)
    def onShelfClickedImportConnectedAssets(self, doubleclick=False):
        sm = self.core.getStateManager()
        if not sm:
            return

        filepath = self.core.getCurrentFileName()
        entity = self.core.getScenefileData(filepath)
        if not entity or entity.get("type") != "shot":
            msg = "Importing connected assets is possible in shot scenefiles only."
            self.core.popup(msg)
            return

        productsToImport = []
        entities = self.core.entities.getConnectedEntities(entity)
        if not entities:
            result = self.core.popupQuestion("No assets are connected to the current shot.", buttons=["Connect Assets...", "Close"], icon=QMessageBox.Information)
            if result == "Connect Assets...":
                self.core.entities.connectEntityDlg(entities=[entity])

            return

        tags = ["usd", "assembly"]
        for centity in entities:
            products = self.core.products.getProductsByTags(centity, tags)
            productsToImport += products

        if not productsToImport:
            msg = "No products to import.\n(checking for tags: \"%s\")" % "\", \"".join(tags)
            self.core.popup(msg)
            return

        for product in productsToImport:
            if "asset_path" not in product:
                continue

            productPath = self.core.products.getLatestVersionpathFromProduct(product["product"], entity=product)
            if not productPath:
                continue

            sm.importFile(productPath)
            logger.debug("added product to shot: %s - %s" % (self.core.entities.getShotName(entity), productPath))

    @err_catcher(name=__name__)
    def getSetPrefix(self):
        return self.core.getConfig("maya", "setPrefix", config="project") or ""

    @err_catcher(name=__name__)
    def getDftStateParent(self, create=True):
        sm = self.core.getStateManager()
        if not sm:
            return

        for state in sm.states:
            if state.ui.listType != "Export" or state.ui.className != "Folder":
                continue

            if state.ui.e_name.text() != "Default States":
                continue

            return state

        if create:
            stateData = {
                "statename": "Default States",
                "listtype": "Export",
                "stateenabled": 2,
                "stateexpanded": False,
            }
            state = sm.createState("Folder", stateData=stateData)
            return state

    @err_catcher(name=__name__)
    def sceneOpen(self, origin):
        if self.core.shouldAutosaveTimerRun():
            origin.startAutosaveTimer()

    @err_catcher(name=__name__)
    def getCurrentFileName(self, origin, path=True):
        import maya.cmds as cmds
        if path:
            filename = cmds.file(q=True, sceneName=True)
            if not filename:
                filename = cmds.file(q=True, location=True)

        else:
            filename = cmds.file(q=True, sceneName=True, shortName=True)
            if not filename:
                filename = cmds.file(q=True, location=True, shortName=True)

        return filename

    @err_catcher(name=__name__)
    def saveScene(self, origin, filepath, details=None, allowChangedExtension=True):
        import maya.cmds as cmds
        import maya.mel as mel
        if not filepath:
            filepath = "untitled"

        if allowChangedExtension:
            saveSceneType = self.core.getConfig("maya", "saveSceneType")
            if saveSceneType == ".ma":
                sType = "mayaAscii"
            elif saveSceneType == ".mb":
                sType = "mayaBinary"
            else:
                curExt = os.path.splitext(self.core.getCurrentFileName())[1]
                if curExt == ".ma":
                    sType = "mayaAscii"
                elif curExt == ".mb":
                    sType = "mayaBinary"
                else:
                    if saveSceneType == ".ma (prefer current scene type)":
                        sType = "mayaAscii"
                    elif saveSceneType == ".mb (prefer current scene type)":
                        sType = "mayaBinary"
                    else:
                        sType = "mayaAscii"

            if sType == "mayaBinary":
                sceneExtension = ".mb"
            else:
                sceneExtension = ".ma"

            filepath = os.path.splitext(filepath)[0] + sceneExtension
        else:
            ext = os.path.splitext(filepath)[1]
            if ext == ".mb":
                sType = "mayaBinary"
            else:
                sType = "mayaAscii"

        cmds.file(rename=filepath)

        try:
            result = cmds.file(save=True, type=sType)
        except:
            return False
        else:
            if not cmds.about(batch=True):
                mel.eval("addRecentFile(\"%s\", \"%s\");" % (filepath, sType))

            return result

    @err_catcher(name=__name__)
    def getFrameRange(self, origin=None):
        import maya.cmds as cmds
        startframe = cmds.playbackOptions(q=True, minTime=True)
        endframe = cmds.playbackOptions(q=True, maxTime=True)

        return [startframe, endframe]

    @err_catcher(name=__name__)
    def getCurrentFrame(self):
        import maya.cmds as cmds
        currentFrame = cmds.currentTime(q=True)
        return currentFrame

    @err_catcher(name=__name__)
    def setFrameRange(self, origin, startFrame, endFrame):
        import maya.cmds as cmds

        cmds.playbackOptions(
            animationStartTime=startFrame,
            animationEndTime=endFrame,
            minTime=startFrame,
            maxTime=endFrame,
        )
        cmds.currentTime(startFrame, edit=True)

    @err_catcher(name=__name__)
    def isNodeValid(self, origin, handle):
        import maya.cmds as cmds
        if "," in handle:
            import mayaUsd
            usdPrim = mayaUsd.ufe.ufePathToPrim(handle)
            valid = usdPrim and usdPrim.IsValid()
        else:
            try:
                valid = len(cmds.ls(handle)) > 0
            except:
                valid = False

        return valid

    @err_catcher(name=__name__)
    def validate(self, string):
        vstr = self.core.validateStr(string, denyChars=["-"])
        return vstr

    @err_catcher(name=__name__)
    def isFbxPluginLoaded(self):
        import maya.mel as mel

        try:
            mel.eval("FBXExtPlugin -l")
            return True
        except:
            pass

        return False        

    @err_catcher(name=__name__)
    def sm_export_exportAppObjects(
        self,
        origin,
        startFrame,
        endFrame,
        outputName,
        nodes=None,
        expType=None,
    ):
        import maya.cmds as cmds
        import maya.mel as mel
        cmds.select(clear=True)
        if nodes is None:
            setName = self.getSetPrefix() + self.validate(origin.getTaskname())
            if not self.isNodeValid(origin, setName):
                return 'Canceled: The selection set "%s" is invalid.' % setName

            cmds.select(cmds.listConnections(setName), noExpand=True)
            expNodes = origin.nodes
        else:
            cmds.select(nodes)
            expNodes = [
                x for x in nodes if "dagNode" in cmds.nodeType(x, inherited=True)
            ]

        if expType is None:
            expType = origin.getOutputType()

        if expType == ".obj":
            self.exportAsObj(
                outputName,
                objects=origin.nodes,
                wholeScene=origin.chb_wholeScene.isChecked(),
                startFrame=startFrame,
                endFrame=endFrame
            )
        elif expType == ".fbx":
            origRange = self.getFrameRange()
            self.setFrameRange(None, startFrame, endFrame)
            fbxKeyframes = os.getenv("PRISM_MAYA_FBX_DELETE_OOR_KEYFRAMES", "0")
            if fbxKeyframes == "1":
                result = "Yes"
            elif fbxKeyframes == "2":
                msg = "By default Maya will export all keyframes to the fbx file even if a framerange is defined.\n\nDo you want to delete all keyframes outside of the defined range? (The scenefile will be reloaded after the publish.)"
                result = self.core.popupQuestion(msg)
            else:
                result = "No"

            if result == "Yes":
                self.deleteOutOfRangeKeys()
                origin.stateManager.reloadScenefile = True

            if not self.isFbxPluginLoaded():
                return "Canceled: The Maya FBX plugin isn't loaded"

            if origin.chb_wholeScene.isChecked():
                mel.eval('FBXExport -f "%s"' % outputName.replace("\\", "\\\\"))
            else:
                prevSel = cmds.ls(selection=True, long=True)
                cmds.select(expNodes)
                mel.eval('FBXExport -f "%s" -s' % outputName.replace("\\", "\\\\"))

                try:
                    cmds.select(prevSel, noExpand=True)
                except:
                    pass

            self.setFrameRange(None, origRange[0], origRange[1])
        elif expType == ".abc":
            wholeScene = origin.chb_wholeScene.isChecked()
            namespaces = origin.chb_exportNamespaces.isChecked()
            result = self.exportAlembic(
                outputName,
                startFrame,
                endFrame,
                nodes=expNodes,
                wholeScene=wholeScene,
                namespaces=namespaces
            )
            if not result:
                return result

        elif expType == ".atom":
            wholeScene = origin.chb_wholeScene.isChecked()
            result = self.exportAtom(
                outputName,
                startFrame,
                endFrame,
                nodes=expNodes,
                wholeScene=wholeScene,
            )
            if not result:
                return result

        elif expType in [".ma", ".mb"]:
            requiresReload = False
            if origin.chb_importReferences.isChecked():
                refFiles = cmds.file(query=True, reference=True)
                prevSel = cmds.ls(selection=True, long=True)

                for i in refFiles:
                    if cmds.file(i, query=True, deferReference=True):
                        msgStr = (
                            'Referenced file "%s" is currently unloaded and cannot be imported.\nWould you like keep or remove this reference in the exported file (it will remain in the working scenefile file) ?'
                            % i
                        )
                        msg = QMessageBox(
                            QMessageBox.Question,
                            "Import Reference",
                            msgStr,
                            QMessageBox.NoButton,
                        )
                        msg.addButton("Keep", QMessageBox.YesRole)
                        msg.addButton("Remove", QMessageBox.YesRole)
                        self.core.parentWindow(msg)
                        result = msg.exec_()

                        if result == 1:
                            cmds.file(i, removeReference=True)
                            requiresReload = True
                    else:
                        cmds.file(i, importReference=True)
                        requiresReload = True
                
                #------------------- ajoute du callback Illogic le callback preExport Illogic ---------------------
                reload(hookPreExport)
                hookPreExport.main(self.core, outputName)
                #------------------- ajoute du callback Illogic le callback preExport Illogic ---------------------

                try:
                    cmds.select(prevSel, noExpand=True)
                except:
                    pass

            if origin.chb_deleteUnknownNodes.isChecked():
                unknownDagNodes = cmds.ls(type="unknownDag")
                unknownNodes = cmds.ls(type="unknown")
                for item in unknownNodes:
                    if cmds.objExists(item):
                        if cmds.lockNode(item, query=True)[0]:
                            cmds.lockNode(item, lock=False)

                        cmds.delete(item)
                        requiresReload = True
                for item in unknownDagNodes:
                    if cmds.objExists(item):
                        if cmds.lockNode(item, query=True)[0]:
                            cmds.lockNode(item, lock=False)

                        cmds.delete(item)
                        requiresReload = True

                self.cleanUnknownPlugins()

            if origin.chb_deleteDisplayLayers.isChecked():
                layers = cmds.ls(type="displayLayer")
                for i in layers:
                    if i != "defaultLayer":
                        cmds.delete(i)
                        requiresReload = True

            if requiresReload:
                origin.stateManager.reloadScenefile = True

            curFileName = self.core.getCurrentFileName()
            if (
                origin.chb_wholeScene.isChecked()
                and os.path.splitext(curFileName)[1] == expType
                and not requiresReload
            ):
                self.core.copySceneFile(curFileName, outputName)
            else:
                if expType == ".ma":
                    typeStr = "mayaAscii"
                elif expType == ".mb":
                    typeStr = "mayaBinary"
                pr = origin.chb_preserveReferences.isChecked()
                try:
                    if origin.chb_wholeScene.isChecked():
                        cmds.file(
                            outputName,
                            force=True,
                            exportAll=True,
                            preserveReferences=pr,
                            type=typeStr,
                        )
                    else:
                        cmds.file(
                            outputName,
                            force=True,
                            exportSelected=True,
                            preserveReferences=pr,
                            type=typeStr,
                        )
                except Exception as e:
                    return "Canceled: %s" % str(e)

                for i in expNodes:
                    if cmds.nodeType(i) == "xgmPalette" and cmds.attributeQuery(
                        "xgFileName", node=i, exists=True
                    ):
                        xgenName = cmds.getAttr(i + ".xgFileName")
                        curXgenPath = os.path.join(
                            os.path.dirname(self.core.getCurrentFileName()), xgenName
                        )
                        tXgenPath = os.path.join(os.path.dirname(outputName), xgenName)
                        shutil.copyfile(curXgenPath, tXgenPath)

        elif expType == ".rs":
            cmds.select(expNodes)
            opt = ""
            if startFrame != endFrame:
                opt = "startFrame=%s;endFrame=%s;frameStep=1;" % (startFrame, endFrame)

            opt += "exportConnectivity=0;enableCompression=0;"

            outputName = os.path.splitext(outputName)[0] + ".####.rs"
            pr = origin.chb_preserveReferences.isChecked()

            if origin.chb_wholeScene.isChecked():
                cmds.file(
                    outputName,
                    force=True,
                    exportAll=True,
                    type="Redshift Proxy",
                    preserveReferences=pr,
                    options=opt,
                )
            else:
                cmds.file(
                    outputName,
                    force=True,
                    exportSelected=True,
                    type="Redshift Proxy",
                    preserveReferences=pr,
                    options=opt,
                )

            outputName = outputName.replace("####", format(endFrame, "04"))
        elif expType == ".ass":
            cmds.select(expNodes)
            opt = ""
            if startFrame != endFrame:
                opt = "-startFrame %s;-endFrame %s;-frameStep 1;" % (startFrame, endFrame)

            opt += "-boundingBox;-fullPath;-lightLinks 1;-shadowLinks 1;-mask 6399"

            outputName = os.path.splitext(outputName)[0] + ".ass"
            pr = origin.chb_preserveReferences.isChecked()

            if origin.chb_wholeScene.isChecked():
                cmds.file(
                    outputName,
                    force=True,
                    exportAll=True,
                    type="ASS Export",
                    preserveReferences=pr,
                    options=opt,
                )
            else:
                cmds.file(
                    outputName,
                    force=True,
                    exportSelected=True,
                    type="ASS Export",
                    preserveReferences=pr,
                    options=opt,
                )

            base, ext = os.path.splitext(outputName)
            if startFrame != endFrame:
                outputName = base + "." + format(endFrame, "04") + ext

        return outputName

    @err_catcher(name=__name__)
    def cleanUnknownPlugins(self):
        import maya.cmds as cmds
        unknownPlugins = cmds.unknownPlugin(q=True, list=True)
        if unknownPlugins:
            for plugin in unknownPlugins:
                cmds.unknownPlugin(plugin, remove=True)

    @err_catcher(name=__name__)
    def exportAsObj(self, outputPath, objects=None, wholeScene=False, startFrame=None, endFrame=None):
        import maya.cmds as cmds

        cmds.loadPlugin("objExport", quiet=True)
        if objects:
            cmds.select(clear=True)
            objNodes = [
                x
                for x in objects
                if cmds.listRelatives(x, shapes=True) is not None
            ]
            cmds.select(objNodes)

        if startFrame is None:
            startFrame = endFrame = int(self.getCurrentFrame())

        for i in range(startFrame, endFrame + 1):
            cmds.currentTime(i, edit=True)
            foutputName = outputPath.replace("####", format(i, "04"))
            if wholeScene:
                cmds.file(
                    foutputName,
                    force=True,
                    exportAll=True,
                    type="OBJexport",
                    options="groups=1;ptgroups=1;materials=1;smoothing=1;normals=1",
                )
            else:
                if cmds.ls(selection=True) == []:
                    return "Canceled: No valid objects are specified for .obj export. No output will be created."
                else:
                    cmds.file(
                        foutputName,
                        force=True,
                        exportSelected=True,
                        type="OBJexport",
                        options="groups=1;ptgroups=1;materials=1;smoothing=1;normals=1",
                    )

        return foutputName

    @err_catcher(name=__name__)
    def deleteOutOfRangeKeys(self):
        import maya.cmds as cmds

        startframe = cmds.playbackOptions(q=True, minTime=True)
        endframe = cmds.playbackOptions(q=True, maxTime=True)
        anim_curves = cmds.ls(type=['animCurveTA', 'animCurveTL', 'animCurveTT', 'animCurveTU'])
        for each in anim_curves:
            try:
                cmds.cutKey(each, time=(-99999, startframe-1), clear=True)
            except:
                pass

            try:
                cmds.cutKey(each, time=(endframe+1, 99999), clear=True)
            except:
                pass

    @err_catcher(name=__name__)
    def getCustomAttributes(self, obj):
        import maya.cmds as cmds

        attrs = []
        mobjs = [obj] + (cmds.listRelatives(obj, children=True, fullPath=True) or [])
        for mobj in mobjs:
            cattrs = cmds.listAttr(mobj, userDefined=True) or []
            for cattr in cattrs:
                if cattr not in attrs:
                    attrs.append(cattr)

        return attrs

    @err_catcher(name=__name__)
    def exportAlembic(self, outputName, startFrame, endFrame, nodes=None, wholeScene=False, namespaces=False):
        import maya.cmds as cmds
        import maya.mel as mel

        rootString = ""
        customAttributes = []
        if wholeScene:
            for obj in cmds.ls(assemblies=True):
                customAttributes += self.getCustomAttributes(obj)
                customAttributes = list(set(customAttributes))
        else:
            rootNodes = [
                x
                for x in nodes
                if len([k for k in nodes if x.rsplit("|", 1)[0] == k]) == 0
            ]
            for i in rootNodes:
                rootString += "-root %s " % i
                customAttributes += self.getCustomAttributes(i)
                customAttributes = list(set(customAttributes))

        expStr = 'AbcExport -j "-frameRange %s %s %s -eulerFilter -worldSpace -uvWrite -writeUVSets -writeVisibility -stripNamespaces -file \\"%s\\""' % (
            startFrame,
            endFrame,
            rootString,
            outputName.replace("\\", "\\\\\\\\"),
        )

        attrStr = ""
        for customAttribute in customAttributes:
            attrStr += "-attr %s " % customAttribute

        expStr = expStr.replace(" -file ", " %s -file " % attrStr)

        if namespaces:
            expStr = expStr.replace("-stripNamespaces", "")

        cmd = {"export_cmd": expStr}
        self.core.callback(name="maya_export_abc", args=[self, cmd])

        logger.debug(cmd["export_cmd"])

        try:
            mel.eval(cmd["export_cmd"])
        except Exception as e:
            if "Conflicting root node names specified" in str(e):
                fString = "You are trying to export multiple objects with the same name, which is not supported in alembic format.\n\nDo you want to export your objects with namespaces?\nThis may solve the problem."
                msg = QMessageBox(QMessageBox.NoIcon, "Export", fString)
                msg.addButton("Export with namesspaces", QMessageBox.YesRole)
                msg.addButton("Cancel export", QMessageBox.YesRole)
                self.core.parentWindow(msg)
                action = msg.exec_()

                if action == 0:
                    cmd = cmd["export_cmd"].replace("-stripNamespaces ", "")
                    try:
                        mel.eval(cmd)
                    except Exception as e:
                        if "Already have an Object named:" in str(e):
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            erStr = "You are trying to export two objects with the same name, which is not supported with the alemic format:\n\n"
                            self.core.popup(erStr + str(e))
                            return False

                else:
                    return False
            else:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.core.popup(str(e))
                return False

        return True

    @err_catcher(name=__name__)
    def exportAtom(self, outputName, startFrame, endFrame, nodes=None, wholeScene=False):
        import maya.cmds as cmds
        cmds.loadPlugin("atomImportExport.mll", quiet=True)
        try:
            cmds.file(
                outputName,
                force=True,
                exportSelected=not wholeScene,
                type="atomExport",
                preserveReferences=True,
                options="statics=1;targetTime=3;selected=childrenToo",
            )
        except Exception as e:
            self.core.popup("Error occured during publish:\n\n%s" % e)
            return False

        return True

    @err_catcher(name=__name__)
    def getRenderLayersFromScene(self):
        import maya.cmds as cmds
        return [
            x
            for x in cmds.ls(type="renderLayer")
            if x in cmds.listConnections("renderLayerManager")
        ]
    
    @err_catcher(name=__name__)
    def getSelectedRenderlayer(self, origin):
        return origin.cb_renderLayer.currentText()

    @err_catcher(name=__name__)
    def deleteNodes(self, origin, handles, num=0):
        import maya.cmds as cmds

        if (num + 1) > len(handles):
            return False

        if self.isNodeValid(origin, handles[num]) and (
            cmds.referenceQuery(handles[num], isNodeReferenced=True)
            or cmds.objectType(handles[num]) == "reference"
        ):
            try:
                refNode = cmds.referenceQuery(
                    handles[num], referenceNode=True, topReference=True
                )
                fileName = cmds.referenceQuery(refNode, filename=True)
            except:
                self.deleteNodes(origin, handles, num + 1)
                return False

            cmds.file(fileName, removeReference=True)
        else:
            for i in handles:
                if not self.isNodeValid(origin, i):
                    continue

                try:
                    cmds.delete(i)
                except RuntimeError as e:
                    if "Cannot delete locked node" in str(e):
                        try:
                            refNode = cmds.referenceQuery(
                                i, referenceNode=True, topReference=True
                            )
                            fileName = cmds.referenceQuery(refNode, filename=True)
                            cmds.file(fileName, removeReference=True)
                        except:
                            pass
                    else:
                        raise e
    
    @err_catcher(name=__name__)
    def sm_playblast_createPlayblast(self, origin, jobFrames, outputName, useAvi=False):
        import maya.cmds as cmds
        import maya.mel as mel
        import maya.OpenMaya as api
        import maya.OpenMayaUI as OpenMayaUI

        self.pbSceneSettings = {}
        if self.core.uiAvailable:
            if origin.curCam is not None and self.isNodeValid(origin, origin.curCam):
                cmds.lookThru(origin.curCam)
                pbCam = origin.curCam
            else:
                view = OpenMayaUI.M3dView.active3dView()
                cam = api.MDagPath()
                view.getCamera(cam)
                pbCam = cam.fullPathName()

            self.pbSceneSettings["pbCam"] = pbCam

            if origin.chb_useRecommendedSettings.isChecked() and self.isNodeValid(None, pbCam) and "," not in pbCam:
                self.pbSceneSettings["filmFit"] = cmds.getAttr(pbCam + ".filmFit")
                self.pbSceneSettings["filmGate"] = cmds.getAttr(
                    pbCam + ".displayFilmGate"
                )
                self.pbSceneSettings["resGate"] = cmds.getAttr(
                    pbCam + ".displayResolution"
                )
                self.pbSceneSettings["overscan"] = cmds.getAttr(pbCam + ".overscan")

                vpName = cmds.getPanel(type="modelPanel")[-1]
                self.pbSceneSettings[
                    "visObjects"
                ] = 'string $editorName = "modelPanel4";\n' + cmds.modelEditor(
                    vpName, q=True, stateString=True
                )

                try:
                    cmds.setAttr(pbCam + ".filmFit", self.playblastSettings["filmFit"])
                except:
                    pass

                try:
                    cmds.setAttr(
                        pbCam + ".displayFilmGate",
                        self.playblastSettings["displayFilmGate"],
                    )
                except:
                    pass

                try:
                    cmds.setAttr(
                        pbCam + ".displayResolution",
                        self.playblastSettings["displayResolution"],
                    )
                except:
                    pass

                try:
                    cmds.setAttr(
                        pbCam + ".overscan", self.playblastSettings["overscan"]
                    )
                except:
                    pass

                if os.getenv("PRISM_MAYA_SET_VISIBLE_OBJECT_TYPES", True) in [True, "1", "True"]:
                    cmds.modelEditor(vpName, e=True, allObjects=False)
                    cmds.modelEditor(vpName, e=True, polymeshes=True)
                    cmds.modelEditor(vpName, e=True, pluginShapes=True)
                    cmds.modelEditor(vpName, e=True, imp=True)

        # set image format to jpeg
        cmds.setAttr(
            "defaultRenderGlobals.imageFormat", self.playblastSettings["imageFormat"]
        )
        outputName = os.path.splitext(outputName)[0].rstrip("#")
        outputName = outputName.strip(".")

        selFmt = origin.cb_formats.currentText()
        if selFmt == ".avi (with audio)":
            fmt = "avi"
            outputName += ".avi"
        elif selFmt == ".qt (with audio)":
            fmt = "qt"
            outputName += ".mov"
        elif selFmt == ".mp4 (with audio)":
            if os.getenv("PRISM_MAYA_PLAYBLAST_MP4_SOURCE_FMT", "avi") == "avi" or useAvi:
                fmt = "avi"
                outputName += ".avi"
            else:
                fmt = "qt"
                outputName += ".mov"
        else:
            fmt = "image"

        showOrnaments = os.getenv("PRISM_MAYA_SHOW_ORNAMENTS", "True")
        aPlayBackSliderPython = mel.eval("$tmpVar=$gPlayBackSlider")
        soundNode = cmds.timeControl(aPlayBackSliderPython, query=True, sound=True)

        cmdString = 'cmds.playblast( startTime=%s, endTime=%s, format="%s", percent=100, viewer=False, forceOverwrite=True, offScreen=True, showOrnaments=%s, filename="%s", sound="%s"' % (
            jobFrames[0],
            jobFrames[1],
            fmt,
            showOrnaments,
            outputName.replace("\\", "\\\\"),
            soundNode,
        )

        if selFmt == ".png":
            cmdString += ", compression=\"png\""

        if origin.chb_resOverride.isChecked():
            cmdString += ", width=%s, height=%s" % (
                origin.sp_resWidth.value(),
                origin.sp_resHeight.value(),
            )
        else:
            if origin.cb_formats.currentText() in [".mp4", ".mp4 (with audio)"]:
                res = self.getViewportResolution()
                if not self.isViewportResolutionEven(res):
                    evenRes = self.getEvenViewportResolution(res)
                    cmdString += ", width=%s, height=%s" % (
                        evenRes["width"],
                        evenRes["height"],
                    )
                    logger.debug("using even resolution to be able to convert to mp4")

        cmdString += ")"
        cmds.currentTime(jobFrames[0], edit=True)

        try:
            eval(cmdString)
        except Exception as e:
            logger.debug(e)

        if len(os.listdir(os.path.dirname(outputName))) < 2 and fmt == "qt":
            if selFmt == ".mp4 (with audio)":
                return self.sm_playblast_createPlayblast(origin, jobFrames, outputName, useAvi=True)
            else:
                self.core.popup(
                    "Couldn't create quicktime video. Make sure quicktime is installed on your system and try again."
                )
        else:
            if selFmt == ".mp4 (with audio)":
                mp4path = os.path.splitext(outputName)[0] + ".mp4"
                result = self.core.media.convertMedia(outputName, 0, mp4path)
                try:
                    os.remove(outputName)
                except:
                    logger.warning("failed to remove file: %s" % outputName)

                outputName = mp4path
            
            if fmt != "image":
                origin.updateLastPath(outputName)


    @err_catcher(name=__name__)
    def getViewportResolution(self, view=None):
        import maya.OpenMayaUI as OpenMayaUI

        if not view:
            view = OpenMayaUI.M3dView.active3dView()
        width = view.portWidth()
        height = view.portHeight()
        return {"width": width, "height": height}

    @err_catcher(name=__name__)
    def isViewportResolutionEven(self, resolution):
        evenRes = self.getEvenViewportResolution(resolution)
        return evenRes == resolution