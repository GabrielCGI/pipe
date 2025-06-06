import json
import os, sys
from functools import partial

import sys

import maya.OpenMayaUI as mui
from maya import cmds
import pymel.core as pm
import pymel.core.datatypes as dt


# Retrieve the version of Maya currently in use
maya_version = cmds.about(version=True)

if maya_version.startswith("2022"):
    # Using PySide2 for Maya 2022
    from PySide2 import QtCore, QtWidgets, QtGui
elif maya_version.startswith("2025"):
    # Using PySide6 for Maya 2025
    # Note: QAction and QShortcut have moved from QtWidgets to QtGui in PySide6
    from PySide6 import QtCore, QtWidgets, QtGui

if maya_version.startswith("2022"):
    # Using Shiboken2 for Maya 2022
    from shiboken2 import wrapInstance
elif maya_version.startswith("2025"):
    # Using Shiboken6 for Maya 2025
    from shiboken6 import wrapInstance

from gf_animUI import object_sets as objSets
from gf_animUI import ui_tools as uiUtils
from gf_animUI import maya_tools as mayaUtils
from gf_animUI import buttons
from gf_animUI.config import version
from gf_animUI.icons import editIcon, editorIcon, showAllIcon, selectAllIcon, newTabIcon, newSelSetIcon, spaceSwitchIcon, \
    resetSelIcon, refreshIcon

button_types = buttons.button_types


def getMayaWindow():
    pointer = mui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget)


# ---- Main Picker UI ---- #
class PickerTab(QtWidgets.QWidget):
    _EDIT = False
    openSetWidgetRequested = QtCore.Signal(pm.PyNode)
    sizeUpdateRequested = QtCore.Signal()

    def __init__(self, tabSet, parent=None):
        super(PickerTab, self).__init__(parent=parent)
        if not isinstance(tabSet, objSets.TabSet):
            raise TypeError('tabSet parameter must be a TabSet, got {} instead'.format(type(tabSet)))

        self._tabSet = tabSet
        self._size = QtCore.QSize(600, 600)

        self.setWindowTitle(self._tabSet.getTitle())

        # ----- Editor ----- #
        self._editor = None

        # ----- Rubber band ----- #
        self.rubberBand = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self.rbOrigin = QtCore.QPoint()
        self._rubberBandActive = False

        # ----- Move buttons ----- #
        self.__mousePressPos = None
        self.__mouseMovePos = None

        # ----- Draw Stuff ----- #
        self._layerDict = {}
        self._layerButtons = {}
        for n, layer in enumerate([self._tabSet] + self._tabSet.getLayers()):
            self._layerDict[layer] = []
            attributes = layer.getButtonAttributes()
            for attr in attributes:
                self._drawButton(attr, layer=layer)

            self.setLayerButton(layer=layer)

    def setLayerButton(self, layer, size=24):
        layers = [self._tabSet] + self._tabSet.getLayers()
        if layer not in layers:
            raise ValueError('{} doesn\'t seem to belong to {}'.format(layer, self._tabSet))
        n = layers.index(layer)

        # Remove previous button if any
        if layer in self._layerButtons:
            self._layerButtons[layer].deleteLater()

        # Create Button
        if layer is self._tabSet:
            deletable = False
        else:
            deletable = True
        layerBtn = buttons.LayerButton(x=size * n, y=0, size=size, color=QtGui.QColor(*layer.getColor()), parent=self)
        layerBtn.deletable = deletable

        # Adjust button display
        layerBtn.show()
        layerBtn.setToolTip('LAYER : {}'.format(layer.name()))
        visState = layer.ui_visibility.get()
        layerBtn.setChecked(visState)
        self.setLayerVisibility(layer, visState)

        # Connect signals
        layerBtn.toggled.connect(lambda x, y=layer: self.setLayerVisibility(y, x))
        layerBtn.toggleAllRequested.connect(lambda l=layer: self.toggleAllLayer(l))
        layerBtn.deleteRequested.connect(lambda l=layer: self.deleteLayer(l))
        layerBtn.editRequested.connect(lambda l=layer: self.editLayer(l))

        # Update Picker's layer related dicts
        self._layerButtons[layer] = layerBtn

        if layer not in self._layerDict:
            self._layerDict[layer] = []

    def paintEvent(self, event):
        super(PickerTab, self).paintEvent(event)
        paint = QtGui.QPainter()
        paint.begin(self)
        bgImg = self._tabSet.background_image.get()
        if bgImg is not None:
            bgImg = bgImg.replace('\\', '/')
            if not os.path.exists(bgImg):
                img = os.path.basename(bgImg)
                if self._tabSet.isReferenced():
                    dir = os.path.dirname(self._tabSet.referenceFile().path)
                else:
                    dir = os.path.dirname(pm.sceneName())
                bgImg = f'{dir}/{img}'

            if os.path.exists(bgImg):
                pixmap = QtGui.QPixmap(bgImg)
                paint.drawPixmap(0,0, pixmap)
                oldSize = self._size
                newSize = pixmap.size()
                self._size = newSize

                if oldSize.width() != newSize.width() and oldSize.height() != newSize.height():
                    self.sizeUpdateRequested.emit()

        paint.end()

    def sizeHint(self):
        return self._size

    def size(self):
        return self._size

    def setEditMode(self, value):
        self._EDIT = value
        buttonList = self.getAllButtons()
        for btn in buttonList:
            btn.setEditMode(value)

        for btn in self._layerButtons.values():
            btn.setEditMode(value)

        if not value:
            for layer in self._layerDict:
                if layer is not self._tabSet:
                    self.setLayerVisibility(layer, layer.ui_visibility.get())

    def setEditor(self, widget=None):
        self._editor = widget

    def createButton(self, x=None, y=None):
        # Gather data
        if self._editor is None:
            return False

        creationData = self._editor.getButtonCreationData()
        node = creationData['node']
        data = creationData['data']
        layer = creationData['layer']

        if x is not None:
            data['x'] = x

        if y is not None:
            data['y'] = y

        if node is None:
            return False

        attr = objSets.addButtonAttributeInstance(node, data)
        layer.addButton(attr)

        self._drawButton(attr, edit=True, layer=layer)
        self._editor.doCycle()

    def _drawButton(self, attr, edit=False, layer=None):
        # Get buttons Data
        data = json.loads(attr.get())
        node = attr.node()
        btnType = data.pop('type', 'default')
        data['parent'] = self

        # Create button
        button = button_types[btnType](**data)
        button.show()
        button.setEditMode(edit)

        # Set button internal data
        button.setInternalData(attr=attr)

        # Attach Command
        cmd = buttons.generateButtonCommand(attr)
        button.clicked.connect(cmd)

        # Set ToolTip
        tTip = buttons.generateToolTip(attr)
        button.setToolTip(tTip)

        # Add to layer
        if layer is None:
            layer = self._tabSet
        if layer not in self._layerDict:
            self._layerDict[layer] = []

        self._layerDict[layer].append(button)
        # Connect edit signal to attribute
        button.buttonEdited.connect(lambda x: attr.set(json.dumps(x)))
        button.shapeChangeRequested.connect(lambda shp: self.changeButtonShape(shp, button))
        button.deleteRequested.connect(lambda: self.deleteButton(button))

        if isinstance(node, pm.nodetypes.ObjectSet):
            button.doubleClicked.connect(lambda: self.openSetWidgetRequested.emit(node))

        return button

    def setLayerVisibility(self, layer, value):
        if layer in self._layerDict:
            layer.ui_visibility.set(value)
            for btn in self._layerDict.get(layer, []):
                btn.setVisible(value)

    def quickCreateSet(self, x=None, y=None):
        if self._editor is None:
            return False

        sel = pm.ls(sl=True)
        if not len(sel):
            return False

        layer = self._editor.getCurrentSet()
        layer.createSelectionSet(nodes=pm.ls(sl=True), select=True)
        self.createButton(x, y)

    # ----- Buttons Operations ----- #
    def getAllButtons(self):
        buttonList = []
        for layer, btns in self._layerDict.items():
            buttonList.extend(btns)
        return buttonList

    def getAllVisibleButtons(self):
        return [btn for btn in self.getAllButtons() if btn.isVisible()]

    def getAllCheckedButtons(self):
        return [btn for btn in self.getAllButtons() if btn.isChecked()]

    def uncheckAllButtons(self):
        for btn in self.getAllCheckedButtons():
            btn.setChecked(False)

    # ---------- Layer Related
    def toggleAllLayer(self, layer):
        buttons = self._layerDict[layer]
        for btn in buttons:
            if btn.isCheckable():
                if btn.isChecked():
                    btn.setChecked(False)
                else:
                    btn.setChecked(True)

    def moveToLayer(self, button, newLayer):
        attr = button.getInternalData()['attr']
        for layer, buttons in self._layerDict.items():
            if button in buttons:
                buttons.remove(button)
                layer.removeButton(attr)

        newLayer.addButton(attr)
        self._layerDict[newLayer].append(button)
        button.setVisible(newLayer.ui_visibility.get())

    def moveSelectedToLayer(self, layer):
        buttons = self.getAllCheckedButtons()
        for btn in buttons:
            self.moveToLayer(btn, layer)

    # ---------- Shape Related
    @mayaUtils.undoChunk
    def changeButtonShape(self, shape, button):
        attr = button.getInternalData()['attr']
        data = json.loads(attr.get())
        data['type'] = shape
        attr.set(json.dumps(data))

        layer = self._tabSet
        for layer, buttons in self._layerDict.items():
            if button in buttons:
                buttons.remove(button)
                break

        button.deleteLater()
        self._drawButton(attr, button._EDIT, layer)

    @mayaUtils.undoChunk
    def changeSelectedShapes(self, shape):
        for btn in self.getAllCheckedButtons():
            self.changeButtonShape(shape, btn)

    # ---------- Delete
    @mayaUtils.undoChunk
    def deleteButton(self, button, confirm=True, deleteSet=False):
        attr = button.getInternalData()['attr']
        node = attr.node()
        if confirm:
            dialog = QtWidgets.QMessageBox.critical(self, 'WARNING !', 'Are you sure you wanna delete this button ?',
                                                    QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel,
                                                    QtWidgets.QMessageBox.Cancel)
            if not dialog == QtWidgets.QMessageBox.Ok:
                return
            if isinstance(node, pm.nodetypes.ObjectSet):
                dialog = QtWidgets.QMessageBox.question(self, 'Deleting Object Set',
                                                        'do you want to delete the following selection set : {}'.format(
                                                            node),
                                                        QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No,
                                                        QtWidgets.QMessageBox.No)
                if dialog == QtWidgets.QMessageBox.Yes:
                    deleteSet = True
                else:
                    deleteSet = False

        attr.remove(b=True)
        if isinstance(node, pm.nodetypes.ObjectSet) and deleteSet:
            pm.delete(node)

        for layer, buttons in self._layerDict.items():
            if button in buttons:
                buttons.remove(button)
                break

        button.deleteLater()

    @mayaUtils.undoChunk
    def deleteSelectedButtons(self, confirm=True):
        if confirm:
            dialog = QtWidgets.QMessageBox.critical(self, 'WARNING !', 'Are you sure you wanna delete these buttons ?',
                                                    QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel,
                                                    QtWidgets.QMessageBox.Cancel)
            if not dialog == QtWidgets.QMessageBox.Ok:
                return

        confirmDeleteSet = True
        deleteSet = False
        for btn in self.getAllCheckedButtons():
            attr = btn.getInternalData()['attr']
            node = attr.node()
            if confirmDeleteSet:
                if isinstance(node, pm.nodetypes.ObjectSet):
                    dialog = QtWidgets.QMessageBox.question(self, 'Deleting Object Set',
                                                            'do you want to delete the following selection set : {}'.format(
                                                                node),
                                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.YesAll | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.NoAll,
                                                            QtWidgets.QMessageBox.No)
                    if dialog in (QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.YesAll):
                        deleteSet = True
                    else:
                        deleteSet = False

                    if dialog in (QtWidgets.QMessageBox.YesAll, QtWidgets.QMessageBox.NoAll):
                        confirmDeleteSet = False

            self.deleteButton(btn, False, deleteSet)

    # ----- Background Image ----- #
    def backgroundImageDialog(self):
        fileName = QtWidgets.QFileDialog.getOpenFileName(self,
                                                         'Open Icon', os.path.dirname(__file__),
                                                         "Image Files (*.png *.jpg *.bmp)")
        if os.path.exists(fileName[0]):
            self._tabSet.background_image.set(fileName[0])
            self.update()
            self.sizeUpdateRequested.emit()

    def removeBackgroundImage(self, confirm=True):
        if confirm:
            dialog = QtWidgets.QMessageBox.critical(self, 'ERMAHGERD !', 'Are you sure you wanna remove the background ?',
                                                    QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel,
                                                    QtWidgets.QMessageBox.Cancel)
            if not dialog == QtWidgets.QMessageBox.Ok:
                return
        self._tabSet.background_image.set('')
        self.update()
        self.sizeUpdateRequested.emit()

    # ----- Mouse Event ----- #
    def mousePressEvent(self, event):
        self.__mousePressPos = None
        self.__mouseMovePos = None

        if not self._EDIT:
            super(PickerTab, self).mousePressEvent(event)

        if self._EDIT:
            if event.button() == QtCore.Qt.RightButton:
                sel = pm.ls(sl=True)
                menu = QtWidgets.QMenu(self)

                localPos = self.mapFromGlobal(event.globalPos())

                if len(sel) > 1:
                    createSet = menu.addAction('Quick Create Set')
                    if self._editor is None:
                        createSet.setEnabled(False)
                    createSet.triggered.connect(lambda: self.quickCreateSet(x=localPos.x(), y=localPos.y()))
                else:
                    createBtn = menu.addAction('Create Button')
                    createBtn.triggered.connect(lambda: self.createButton(x=localPos.x(), y=localPos.y()))
                    if len(sel) != 1:
                        createBtn.setEnabled(False)

                menu.addSection('Edit Tab')
                bgImgAction = menu.addAction('Background image...')
                bgImgAction.triggered.connect(self.backgroundImageDialog)

                removeBgImg = menu.addAction('Remove background')
                removeBgImg.triggered.connect(self.removeBackgroundImage)

                deleteAction = menu.addAction('Delete tab')
                deleteAction.triggered.connect(self.deleteTab)

                menu.addSection('Edit Selected Buttons')
                bActionEnbable = True if len(self.getAllCheckedButtons()) else False
                moveSelectedMenu = menu.addMenu('Change layer')
                moveSelectedMenu.setEnabled(bActionEnbable)
                for layer in self._layerDict.keys():
                    action = moveSelectedMenu.addAction(layer.name())
                    # action.triggered.connect(lambda l=layer: self.moveSelectedToLayer(l))
                    action.triggered.connect(partial(self.moveSelectedToLayer, layer))

                deleteSelectedAction = menu.addAction('Delete buttons')
                deleteSelectedAction.setEnabled(bActionEnbable)
                deleteSelectedAction.triggered.connect(self.deleteSelectedButtons)

                shpMenu = menu.addMenu('Change Shape')
                shpMenu.setEnabled(bActionEnbable)
                shapeNames = button_types.keys()
                for shp in shapeNames:
                    action = shpMenu.addAction(shp)
                    # action.triggered.connect(lambda s=shp: self.changeSelectedShapes(s))
                    action.triggered.connect(partial(self.changeSelectedShapes, shp))

                menuAction = menu.addMenu(buttons.CustomButton.getEditMenu(self.getAllCheckedButtons(), self))
                menuAction.setText('Edit buttons')
                menuAction.setEnabled(bActionEnbable)

                menu.exec_(event.globalPos())

            if event.buttons() == QtCore.Qt.MidButton:
                self.__mousePressPos = event.globalPos()
                self.__mouseMovePos = event.globalPos()

        if event.button() == QtCore.Qt.LeftButton:
            self._rubberBandActive = True
            self.rbOrigin = QtCore.QPoint(event.pos())
            self.rubberBand.setGeometry(QtCore.QRect(self.rbOrigin, QtCore.QSize()))
            self.rubberBand.show()

    def mouseMoveEvent(self, event):
        if self._rubberBandActive:
            self.rubberBand.setGeometry(QtCore.QRect(self.rbOrigin, event.pos()).normalized())

        if self._EDIT and event.buttons() == QtCore.Qt.MidButton:
            globalPos = event.globalPos()
            diff = globalPos - self.__mouseMovePos
            for btn in self.getAllCheckedButtons():
                btn.moveBy(diff)

            self.__mouseMovePos = globalPos

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self._rubberBandActive:
            buttons = self.getAllVisibleButtons()
            rbRect = self.rubberBand.geometry()
            self.setFocus()
            rbTriggerList = []
            for btn in buttons:
                bRect = btn.geometry()
                if rbRect.intersects(bRect):
                    rbTriggerList.append(btn)
            if not self._EDIT or QtGui.QGuiApplication.keyboardModifiers() == QtCore.Qt.AltModifier:
                self._triggerButtonsRbCmd(rbTriggerList)
            else:
                self._triggerButtonsEditRbCmd(rbTriggerList)
            self.rubberBand.hide()
            self._rubberBandActive = False

        if self.__mousePressPos is not None:
            moved = event.globalPos() - self.__mousePressPos
            if moved.manhattanLength() > 3:
                event.ignore()
                with pm.UndoChunk():
                    for btn in self.getAllCheckedButtons():
                        btn.buttonEdited.emit(btn.getData())
                return

    # ----- RubberBand functions ----- #
    def _triggerButtonsEditRbCmd(self, buttons):
        if QtGui.QGuiApplication.keyboardModifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
            for btn in buttons:
                btn.setChecked(True)
        elif QtGui.QGuiApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
            for btn in buttons:
                btn.setChecked(False)
        elif QtGui.QGuiApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
            for btn in buttons:
                btn.setChecked(False if btn.isChecked() else True)
        elif QtGui.QGuiApplication.keyboardModifiers() == QtCore.Qt.NoModifier:
            self.uncheckAllButtons()
            for btn in buttons:
                btn.setChecked(True)

    @mayaUtils.undoChunk
    def _triggerButtonsRbCmd(self, buttons):
        if not len(buttons):
            pm.select(clear=True)

        selectList = [btn.getInternalData()['attr'].node() for btn in buttons if btn.getData()['commandType'] == 'select']
        if QtGui.QGuiApplication.keyboardModifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
            pm.select(selectList, add=True)
        elif QtGui.QGuiApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
            pm.select(selectList, d=True)
        elif QtGui.QGuiApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
            pm.select(selectList, tgl=True)
        else:
            pm.select(selectList)

    # ----- Layer Edit ----- #
    def deleteTab(self, confirm=True):
        if confirm:
            dialog = QtWidgets.QMessageBox.critical(self, 'ERMAHGERD !', 'Are you sure you wanna delete this entire tab ?',
                                                    QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel,
                                                    QtWidgets.QMessageBox.Cancel)
            if not dialog == QtWidgets.QMessageBox.Ok:
                return
        self._tabSet.cleanDelete()
        self.deleteLater()

    def deleteLayer(self, layer, confirm=True):
        if confirm:
            dialog = QtWidgets.QMessageBox.critical(self, 'ERMAHGERD !', 'Are you sure you wanna delete this entire layer ?',
                                                    QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel,
                                                    QtWidgets.QMessageBox.Cancel)
            if not dialog == QtWidgets.QMessageBox.Ok:
                return
        lBtn = self._layerButtons[layer]
        buttons = self._layerDict[layer]
        for btn in buttons:
            btn.deleteLater()
        layer.cleanDelete()
        lBtn.deleteLater()
        del self._layerButtons[layer], self._layerDict[layer]

    def editLayer(self, layer):
        dialog = CreateLayerWidget(parent=self)
        dialog.setTitle(layer.getTitle())
        dialog.setName(layer.name())
        dialog.setVector(layer.getColor())
        dialog.exec_()
        if dialog.result() == dialog.Accepted:
            layer.editParameters(name=dialog.getName(),
                                 title=dialog.getTitle(),
                                 color=dialog.getColorNormalizedVector())
            self.setLayerButton(layer)


class AnimWindow(QtWidgets.QMainWindow):
    _EDIT = False

    def __init__(self, masterSet, showEditToolBar=False):
        if not isinstance(masterSet, objSets.MasterSet):
            raise TypeError('masterSet parameter must be a MasterSet, got {} instead'.format(type(masterSet)))

        self._masterSet = masterSet
        self._tabSets = self._masterSet.getTabs()

        winName = '{}_AnimUI'.format(masterSet.name())
        winTitle = '{title}'.format(title=masterSet.getTitle())

        mayaMainWindow = getMayaWindow()

        # check if window already exists:
        for win in mayaMainWindow.findChildren(QtWidgets.QWidget, winName):
            win.close()

        super(AnimWindow, self).__init__(mayaMainWindow)

        # ----- Setup window ----- #
        self.setObjectName(winName)
        self.setWindowTitle(winTitle)
        self.setDockOptions(QtWidgets.QMainWindow.ForceTabbedDocks | QtWidgets.QMainWindow.VerticalTabs)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        mainWidget = QtWidgets.QWidget()
        self.setCentralWidget(mainWidget)
        self._layout = QtWidgets.QVBoxLayout(mainWidget)
        self.setIconSize(QtCore.QSize(40, 40))

        # ----- Pickers TabWidget ----- #
        self.pickersTab = QtWidgets.QTabWidget()
        self.pickersTab.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.pickersTab.currentChanged.connect(self._updatePickersTabSize)
        self.pickersTab.resize(QtCore.QSize(600,600))
        self._layout.addWidget(self.pickersTab)

        self._tabWidgets = []
        for tabSet in self._tabSets:
            self._addTabSet(tabSet)
        # Dock Widgets
        self.controllersListDockWidget = QtWidgets.QDockWidget()
        self.controllersListDockWidget.setWindowTitle('Controllers')
        self.selAllWidget = self.createSelectAllWidget()
        self.controllersListDockWidget.setWidget(self.selAllWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.controllersListDockWidget)
        self.selAllWidget.visibilityChanged.connect(self._updatePickersTabSize)
        self.controllersListDockWidget.setVisible(False)

        spaceswitch_area = QtCore.Qt.RightDockWidgetArea
        self.spaceSwitchDockWidget = QtWidgets.QDockWidget()
        self.spaceSwitchWidget = self.createSpaceSwitchWidget(horizontal=False)
        self.spaceSwitchDockWidget.setWindowTitle('Space Switches')
        self.spaceSwitchDockWidget.setWidget(self.spaceSwitchWidget)
        self.addDockWidget(spaceswitch_area, self.spaceSwitchDockWidget)
        self.spaceSwitchDockWidget.setVisible(False)

        # ----- ToolBars ----- #
        self.toolbar_area = QtCore.Qt.LeftToolBarArea
        self.editToolBar = QtWidgets.QToolBar('Edit Tools')
        self.addToolBar(self.toolbar_area, self.editToolBar)

        editAction = self.editToolBar.addAction(editIcon, 'Edit')
        editAction.setCheckable(True)
        editAction.toggled.connect(self.setEditMode)

        editorAction = self.editToolBar.addAction(editorIcon, 'Editor')
        editorAction.triggered.connect(partial(self.openEditor, True))

        newSetAction = self.editToolBar.addAction(newSelSetIcon, 'Select Set')
        newSetAction.triggered.connect(self.newSetDialog)

        newTabAction = self.editToolBar.addAction(newTabIcon, 'New Tab')
        newTabAction.triggered.connect(self.newTabDialog)

        if not showEditToolBar:
            self.editToolBar.hide()

        for action in [editorAction, newSetAction, newTabAction]:
            editAction.toggled.connect(action.setEnabled)
        editAction.toggled.emit(False)

        self.toolBar = QtWidgets.QToolBar('Anim Tools')
        self.addToolBar(self.toolbar_area, self.toolBar)
        self.openCtrListAction = self.toolBar.addAction(showAllIcon, 'Ctr List')
        self.openCtrListAction.setCheckable(True)
        self.openCtrListAction.toggled.connect(self.controllersListDockWidget.setVisible)

        self.selAllAction = self.toolBar.addAction(selectAllIcon, 'Select All\nSHIFT : Add to current selection')
        self.selAllAction.triggered.connect(self.selectAll)

        self.openSpaceSwitch = self.toolBar.addAction(spaceSwitchIcon, 'Space Switch')
        self.openSpaceSwitch.setCheckable(True)
        self.openSpaceSwitch.toggled.connect(self.spaceSwitchDockWidget.setVisible)
        self.openSpaceSwitch.toggled.connect(self.adjustSize)

        self.resetSelAction = self.toolBar.addAction(resetSelIcon, 'Reset Selection\nSHIFT : Reset transform values only')
        self.resetSelAction.triggered.connect(self.resetSelection)

        # ----- Extra Tools ----- #
        self.toolsWidget = None
        self.customToolBar = None

        self._updatePickersTabSize()

    @classmethod
    def list(cls):
        widgets = getMayaWindow().findChildren(AnimWindow)
        return widgets

    def setEditMode(self, value):
        self._EDIT = value
        for widget in self._tabWidgets:
            widget.setEditMode(value)
        # self.selAllWidget.setEditMode(value)
        self.spaceSwitchWidget.setEditMode(value)
        for dw in self.findChildren(QtWidgets.QDockWidget):
            widget = dw.widget()
            if isinstance(widget, SetListWidget):
                widget.setEditMode(value)

    @mayaUtils.undoChunk
    def _initSelectAllSet(self):
        objSet = self._masterSet._addSelectAllSet()
        self._masterSet.fillSelectAllSet(pm.ls(sl=True), replace=True)
        self.selAllWidget.setObjSet(objSet)

    @mayaUtils.undoChunk
    def _initSpaceSwitchSet(self, attributes):
        objSet = self._masterSet._addSpaceSwitchSet()
        self._masterSet.fillSpaceSwitchSet(attributes, replace=True)
        self.spaceSwitchWidget.setObjSet(objSet)

    # ----- Tools Widget ----- #
    def createSpaceSwitchWidget(self, horizontal):
        spaceSwitchWidget = SpaceSwitchWidget(self._masterSet._getSpaceSwitchSet(), parent=self, horizontal=horizontal)
        spaceSwitchWidget.createRequested.connect(self._initSpaceSwitchSet)
        return spaceSwitchWidget

    def createSelectAllWidget(self):
        selAllWidget = SetListWidget(self._masterSet._getSelectAllSet())
        selAllWidget.createRequested.connect(self._initSelectAllSet)
        return selAllWidget

    def initToolsWidget(self):
        if self.toolsWidget is None:
            self.toolsWidget = QtWidgets.QSplitter(QtCore.Qt.Vertical, parent=self)
            self.pickersTab.insertTab(0, self.toolsWidget, 'Tools')
        return self.toolsWidget

    def initCustomToolBar(self):
        if self.customToolBar is None:
            self.customToolBar = QtWidgets.QToolBar('Custom Tools')
        self.addToolBar(self.toolbar_area, self.customToolBar)
        return self.customToolBar

    # ----- Editor Related ----- #
    def openEditor(self, allowCycle=True):
        # Look for existing editor
        editor = self.getCurrentEditor()
        if editor is not None:
            editor.show()
            return editor

        # Create a new editor if none exists
        activePicker = self.pickersTab.currentWidget()
        uiSet = activePicker._tabSet
        editor = AnimEditor(uiSet=uiSet, allowCycle=allowCycle, parent=self)

        # Register this editor in all tabWidgets
        for tabWidget in self._tabWidgets:
            tabWidget.setEditor(self.getCurrentEditor())

        editor.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.pickersTab.currentChanged.connect(
            lambda x: editor.setTabSet(self.pickersTab.widget(x)._tabSet) if isinstance(self.pickersTab.widget(x), PickerTab) else False)
        editor.show()
        # editor.buttonCreated.connect(
        #     lambda x: self.pickersTab.currentWidget()._drawButton(x, edit=self.pickersTab.currentWidget()._EDIT,
        #                                                           layer=editor.getCurrentSet()) if self.pickersTab.currentWidget() is not None else False)
        editor.buttonCreateRequest.connect(lambda: self.pickersTab.currentWidget().createButton())
        editor.cycleTriggered.connect(self.selAllWidget.selectNext)
        editor.copyButtonDataRequested.connect(lambda: self._sendSelectedButtonDataToEditor(editor))
        editor.layerCreated.connect(lambda x: self.pickersTab.currentWidget().setLayerButton(x) if self.pickersTab.currentWidget() is not None else False)
        return editor

    def getCurrentEditor(self):
        editors = self.findChildren(AnimEditor)
        if len(editors):
            return editors[0]
        return None

    def _sendSelectedButtonDataToEditor(self, editor):
        wIdx = self.pickersTab.currentIndex()
        if wIdx == -1:
            return False

        picker = self.pickersTab.currentWidget()
        checkedButtons = picker.getAllCheckedButtons()
        if len(checkedButtons):
            editor.updateButtonOptions(checkedButtons[0].getData())
            picker.uncheckAllButtons()

    def newSetDialog(self):
        # Create Dialog
        dialog = CreateSetWidget(hasTitle=False, parent=self)
        dialog.setWindowTitle('New Selection Set')
        layerWidget = LayerWidget(self.pickersTab.currentWidget()._tabSet)
        layerWidget.layerCreated.connect(lambda x: self.pickersTab.currentWidget().setLayerButton(x) if self.pickersTab.currentWidget() is not None else False)
        self.pickersTab.currentChanged.connect(lambda x: layerWidget.setTabSet(self.pickersTab.widget(x)._tabSet))
        dialog._layout.insertWidget(0, layerWidget)
        dialog.accepted.connect(lambda: layerWidget.getCurrentSet().createSelectionSet(nodes=pm.ls(sl=True), name=dialog.getName(), select=True))

        # Match current layer with current editor if applicable
        editor = self.getCurrentEditor()
        if editor is not None:
            layerWidget.layerBox.setCurrentText(editor.layerWidget.layerBox.currentText())

        dialog.exec_()
        if dialog.result() == QtWidgets.QDialog.Accepted:
            layer = layerWidget.getCurrentSet()
            editor = self.openEditor(True)
            editor.layerWidget.setCurrentSet(layer)

    # ----- Tab Related ----- #
    def _addTabSet(self, tabSet):
        tabWidget = PickerTab(tabSet)
        tabWidget.setEditor(self.getCurrentEditor())
        self.pickersTab.addTab(tabWidget, tabSet.getTitle())
        self._tabWidgets.append(tabWidget)
        tabWidget.openSetWidgetRequested.connect(self.openSetWidget)
        tabWidget.sizeUpdateRequested.connect(self._updatePickersTabSize)
        tabWidget.setEditMode(self._EDIT)
        self._updatePickersTabSize()

    def _updatePickersTabSize(self, *args, **kwargs):
        idx = self.pickersTab.currentIndex()
        # if idx == -1:
        #     self.pickersTab.setFixedSize(QtCore.QSize(600, 600))
        # else:
        #     widget = self.pickersTab.widget(idx)
        #     self.pickersTab.setFixedSize(widget.size())
        self.pickersTab.adjustSize()
        self.adjustSize()

    def newTabDialog(self):
        dialog = CreateSetWidget()
        dialog.accepted.connect(lambda: self.newTab(*dialog.getValues()))
        dialog.exec_()

    def newTab(self, name, title):
        tab = self._masterSet.newTab(name, title)
        self._addTabSet(tab)

    # ----- Maya Tools ----- #
    @mayaUtils.undoChunk
    def selectAll(self):
        selAllSet = self._masterSet._getSelectAllSet()
        if selAllSet is None:
            return

        mod = QtGui.QGuiApplication.keyboardModifiers()
        if mod == QtCore.Qt.ShiftModifier:
            pm.select(selAllSet, add=True)
        else:
            pm.select(selAllSet)

    @mayaUtils.undoChunk
    def resetSelection(self):
        sel = pm.ls(sl=True)
        ud = False if QtGui.QGuiApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier else True
        mayaUtils.resetAttributes(nodeList=sel, ud=ud)

    def openSetWidget(self, objSet):
        # Check if that set is already open
        for dw in self.findChildren(QtWidgets.QDockWidget):
            widget = dw.widget()
            if isinstance(widget, SetListWidget):
                if widget.objSet == objSet:
                    dw.raise_()
                    return
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle(objSet.name())
        dock.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        widget = SetListWidget(objSet)
        widget.setEditMode(self._EDIT)
        dock.setWidget(widget)
        self.tabifyDockWidget(self.controllersListDockWidget, dock)
        widget.visibilityChanged.connect(self._updatePickersTabSize)
        return dock, widget


class DockedAnimWindow(AnimWindow):
    def __init__(self, masterSet, showEditToolBar=False):
        super(DockedAnimWindow, self).__init__(masterSet=masterSet, showEditToolBar=showEditToolBar)
        self.toolbar_area = QtCore.Qt.BottomToolBarArea
        self.addToolBar(self.toolbar_area, self.editToolBar)
        self.addToolBar(self.toolbar_area, self.toolBar)

        self.toolBar.removeAction(self.openSpaceSwitch)
        self.spaceSwitchWidget.deleteLater()

        # ----- Tools Widget ----- #
        self.initToolsWidget()

        self.dock = dockWidget(self)

        self.controllersListDockWidget.setFloating(True)
        self.controllersListDockWidget.setWindowTitle('{}:{}'.format(self.windowTitle(), self.controllersListDockWidget.windowTitle()))

    def openSetWidget(self, objSet):
        dock, widget = super(DockedAnimWindow, self).openSetWidget(objSet=objSet)
        dock.setFloating(True)

    def initToolsWidget(self):
        super(DockedAnimWindow, self).initToolsWidget()
        self.spaceSwitchWidget = self.createSpaceSwitchWidget(horizontal=True)
        self.toolsWidget.addWidget(self.spaceSwitchWidget)

    def close(self):
        super(DockedAnimWindow, self).close()
        self.dock.deleteLater()


class AnimEditor(QtWidgets.QDialog):
    buttonCreated = QtCore.Signal(pm.Attribute)
    buttonCreateRequest = QtCore.Signal()
    cycleTriggered = QtCore.Signal()
    copyButtonDataRequested = QtCore.Signal()

    def __init__(self, uiSet, allowCycle=True, parent=None):
        super(AnimEditor, self).__init__(parent=parent)
        if not isinstance(uiSet, (objSets.TabSet)):
            raise TypeError('tabSet parameter must be a TabSet, got {} instead'.format(type(uiSet)))

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setAlignment(QtCore.Qt.AlignTop)
        self._layout.setSpacing(10)

        self._currentBtn = None
        self._currentOptions = None
        self._tabSet = None

        self._previousBtnData = {}

        # ----- Auto Cycle ----- #
        self.cycleCbx = QtWidgets.QCheckBox('Auto-Cycle')
        self.cycleCbx.setChecked(True)
        self._layout.addWidget(self.cycleCbx)
        if not allowCycle:
            self.cycleCbx.setChecked(False)
            self.cycleCbx.setDisabled(True)

        # ----- Current Selection ----- #
        self.curSelWidget = uiUtils.LabeledField(name='Node')
        self.curSelLabel = uiUtils.CurrentSelectionLabel()
        self.curSelWidget.setField(self.curSelLabel)
        self._layout.addWidget(self.curSelWidget)

        # ----- Layer ----- #
        self.layerWidget = LayerWidget(uiSet)
        self.layerCreated = self.layerWidget.layerCreated
        self._layout.addWidget(self.layerWidget)

        # ----- Load Selected ----- #
        copySelBtn = QtWidgets.QPushButton('Copy selected')
        self._layout.addWidget(copySelBtn)
        copySelBtn.clicked.connect(self.copyButtonDataRequested.emit)

        # ----- Type ----- #
        typeWidget = uiUtils.LabeledField(name='Type')
        self._layout.addWidget(typeWidget)
        self.typeBox = QtWidgets.QComboBox()
        self.typeBox.setMaximumWidth(200)
        self.typeBox.addItems(['default', 'rounded', 'polygon', 'ellipse'])
        typeWidget.setField(self.typeBox)
        self.typeBox.currentTextChanged.connect(self._loadButtonOptions)
        self.typeBox.currentTextChanged.emit('default')

        # ----- Buttons ----- #
        btnLayout = QtWidgets.QHBoxLayout(self)
        self._layout.addLayout(btnLayout)
        btnLayout.setAlignment(QtCore.Qt.AlignCenter)
        btnLayout.setContentsMargins(0, 0, 0, 0)

        createBtn = QtWidgets.QPushButton('Create')
        btnLayout.addWidget(createBtn)
        createBtn.clicked.connect(self.buttonCreateRequest.emit)
        self.curSelLabel.validSelection.connect(createBtn.setEnabled)

        closeBtn = QtWidgets.QPushButton('Close')
        btnLayout.addWidget(closeBtn)
        closeBtn.clicked.connect(self.close)

        self.setTabSet(uiSet)

    def _loadButtonOptions(self, btnType):
        data = {}
        if self._currentBtn is not None:
            data.update(self._currentBtn.getData())
        data['type'] = btnType
        self.updateButtonOptions(data)

    def updateButtonOptions(self, data):
        self._clearButtonOptions()
        data['parent'] = self
        btnType = data.get('type', 'default')

        # Update typeBox
        self.typeBox.blockSignals(True)
        self.typeBox.setCurrentText(btnType)
        self.typeBox.blockSignals(False)

        Button = button_types.get(btnType, buttons.CustomButton)
        self._currentBtn = Button(**data)
        self._currentOptions = self._currentBtn.getOptionsWidget()[0]
        self._layout.insertWidget(5, self._currentOptions)
        self._layout.insertWidget(6, self._currentBtn)

    def _clearButtonOptions(self):
        if self._currentBtn is not None:
            self._previousBtnData = self._currentBtn.getData()
            self._currentBtn.setParent(None)
            self._currentBtn = None

        if self._currentOptions is not None:
            self._currentOptions.setParent(None)
            self._currentOptions = None

    def getCurrentSet(self):
        return self.layerWidget.getCurrentSet()

    def setTabSet(self, tabSet):
        if not isinstance(tabSet, (objSets.TabSet)):
            raise TypeError('tabSet parameter must be a TabSet, got {} instead'.format(type(tabSet)))

        self._tabSet = tabSet
        self.setWindowTitle('Editing : {}'.format(self._tabSet.name()))
        self.layerWidget.setTabSet(self._tabSet)

    def getButtonCreationData(self):
        sel = pm.ls(sl=True)
        result = {'data': self._currentBtn.getData(),
                  'layer': self.getCurrentSet(),
                  'node': sel[0] if len(sel) else None}
        return result

    @mayaUtils.undoChunk
    def createButton(self):
        # TODO: Change this so that it only returns the data to create the button, instead of creating the button itself
        # TODO : Handle the button creation directly in the Picker Tab
        if self._currentBtn is None:
            return None
        sel = pm.ls(sl=True)

        if not len(sel):
            return None

        createData = {'data': self._currentBtn.getData(),
                      'layer': self.getCurrentSet()}
        uiSet = self.getCurrentSet()
        data = self._currentBtn.getData()
        attr = objSets.addButtonAttributeInstance(sel[0], data)
        uiSet.addButton(attr)
        self.buttonCreated.emit(attr)

        # Cycle through 'select all' list
        self.doCycle()
        return attr

    def doCycle(self):
        if self.cycleCbx.isChecked():
            self.cycleTriggered.emit()


# ---- Launcher ---- #
class AnimLauncherDialog(QtWidgets.QDialog):
    def __init__(self, ui_widget=AnimWindow):
        winName = 'anim_launcher_dialog'
        winTitle = 'Gf Anim UI {}'.format(version)

        mayaMainWindow = getMayaWindow()

        # check if window already exists:
        for win in mayaMainWindow.findChildren(QtWidgets.QWidget, winName):
            win.close()

        super(AnimLauncherDialog, self).__init__(getMayaWindow())

        self._masterSets = []

        self.ui_widget = ui_widget

        # ----- Setup window ----- #
        self.setObjectName(winName)
        self.setWindowTitle(winTitle)
        self._layout = QtWidgets.QVBoxLayout(self)

        menuBar = QtWidgets.QMenuBar()
        self._layout.setMenuBar(menuBar)
        menu = menuBar.addMenu('Menu')
        newUiAction = menu.addAction('New')
        newUiAction.triggered.connect(self.newUIDialog)

        deleteUiAction = menu.addAction('Delete')
        deleteUiAction.triggered.connect(self.deleteUIDialog)

        importUiAction = menu.addAction('Import...')
        importUiAction.triggered.connect(self.importUIDialog)

        exportUiAction = menu.addAction('Export...')
        exportUiAction.triggered.connect(self.exportUIDialog)

        setsWidget = uiUtils.CompactLabeledField('UI')
        self.setBox = QtWidgets.QComboBox()
        self.setBox.setMaximumWidth(200)
        setsWidget.setField(self.setBox)

        refreshButton = QtWidgets.QPushButton()
        refreshButton.setIcon(refreshIcon)
        refreshButton.setIconSize(QtCore.QSize(20,20))
        refreshButton.setFixedSize(QtCore.QSize(20,20))
        setsWidget.layout.insertWidget(0, refreshButton)
        refreshButton.clicked.connect(self.loadMasterSets)

        openUIButton = QtWidgets.QPushButton('Open')
        openUIButton.setFixedWidth(50)
        setsWidget.layout.addWidget(openUIButton)
        openUIButton.clicked.connect(lambda: self.openSetUI(self.getCurrentSet()) if len(self._masterSets) else False)

        self._layout.addWidget(setsWidget)
        self.loadMasterSets()

    @classmethod
    def list(cls):
        widgets = getMayaWindow().findChildren(AnimLauncherDialog)
        return widgets

    def getCurrentSet(self):
        if len(self._masterSets):
            return self._masterSets[self.setBox.currentIndex()]
        else:
            return None

    def newUIDialog(self):
        dialog = CreateSetWidget(parent=self)
        dialog.accepted.connect(lambda: self.createMasterSet(dialog.getName(), dialog.getTitle()))
        dialog.exec_()

    def deleteUIDialog(self):
        dialog = QtWidgets.QMessageBox.critical(self, 'WARNING !', 'Are you sure you wanna delete this button ?',
                                                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
                                                QtWidgets.QMessageBox.Cancel)
        if not dialog == QtWidgets.QMessageBox.Ok:
            return

        self.getCurrentSet().cleanDelete()
        self.loadMasterSets()

    def exportUIDialog(self):
        currentSet = self.getCurrentSet()
        if currentSet is None:
            return

        outFile = exportObjectSetDialog(currentSet, self)
        return outFile

    def importUIDialog(self):
        dialog = ImportMasterSetDialog(self)
        dialog.show()
        dialog.setCreated.connect(self.openSetUI)
        dialog.accepted.connect(self.loadMasterSets)

    @mayaUtils.undoChunk
    def createMasterSet(self, name, title):
        mSet = objSets.MasterSet(name=name, title=title)
        self.loadMasterSets()
        self.openSetUI(mSet, True)

    def loadMasterSets(self):
        sys.stdout.write('Reloading UI list...\n')
        self._masterSets = objSets.MasterSet.list()
        sys.stdout.write('{}\n'.format(self._masterSets))
        self.setBox.clear()

        for mSet in self._masterSets:
            self.setBox.addItem('{name} / {title}'.format(name=mSet.name(), title=mSet.getTitle()))
            sys.stdout.write('Loading {name} / {title}\n'.format(name=mSet.name(), title=mSet.getTitle()))
        self.setBox.update()

    @mayaUtils.undoChunk
    def openSetUI(self, mSet,  showEditToolBar=False):
        ui = self.ui_widget(mSet, showEditToolBar)
        ui.show()


# ---- Base Set Creator UI ---- #
class CreateSetWidget(QtWidgets.QDialog):
    def __init__(self, hasTitle=True, parent=None):
        super(CreateSetWidget, self).__init__(parent=parent)
        self.setWindowTitle('Set Options')
        self._layout = QtWidgets.QVBoxLayout(self)
        self._hasTitle = hasTitle
        # ----- QLineEdits ----- #
        nameWidget = uiUtils.LabeledField('Name')
        self.nameField = QtWidgets.QLineEdit()
        self.nameField.setMaximumWidth(200)
        nameWidget.setField(self.nameField)
        self._layout.addWidget(nameWidget)

        if self._hasTitle:
            titleWidget = uiUtils.LabeledField('Title')
            self.titleField = QtWidgets.QLineEdit()
            self.titleField.setMaximumWidth(200)
            titleWidget.setField(self.titleField)
            self._layout.addWidget(titleWidget)

            self.nameField.textChanged.connect(self.titleField.setText)

        # ----- Buttons ----- #
        btnLayout = QtWidgets.QHBoxLayout(self)
        self._layout.addLayout(btnLayout)
        btnLayout.setAlignment(QtCore.Qt.AlignLeft)
        btnLayout.setContentsMargins(0, 0, 0, 0)

        createBtn = QtWidgets.QPushButton('Ok')
        btnLayout.addWidget(createBtn)
        createBtn.clicked.connect(self.accept)

        closeBtn = QtWidgets.QPushButton('Cancel')
        btnLayout.addWidget(closeBtn)
        closeBtn.clicked.connect(self.reject)

    def getName(self):
        return self.nameField.text()

    def getTitle(self):
        if self._hasTitle:
            return self.titleField.text()
        return self.getName()

    def getValues(self):
        return self.getName(), self.getTitle()

    def setName(self, value):
        self.nameField.setText(value)

    def setTitle(self, value):
        if self._hasTitle:
            self.titleField.setText(value)
            self.nameField.textChanged.disconnect()


class CreateLayerWidget(CreateSetWidget):
    def __init__(self, hasTitle=True, parent=None):
        super(CreateLayerWidget, self).__init__(hasTitle, parent)
        self.setWindowTitle('Layer Options')
        # Color Field
        colorWidget = uiUtils.LabeledField('Color')
        self.colorField = uiUtils.ColorPickerField(QtGui.QColor(250, 125, 75))
        colorWidget.setField(self.colorField)
        self._layout.insertWidget(2, colorWidget)

    def getColor(self):
        return self.colorField.color()

    def getColorVector(self):
        return self.colorField.asVector()

    def getColorNormalizedVector(self):
        return self.colorField.asNormalizedVector()

    def setColor(self, value=QtGui.QColor()):
        self.colorField.setColor(value)

    def setVector(self, value=dt.Vector()):
        self.colorField.setVector(value)

    def getValues(self):
        name, title = super(CreateLayerWidget, self).getValues()
        return name, title, self.getColorNormalizedVector()


# ---- Layers List ---- #
class LayerWidget(uiUtils.LabeledField):
    layerCreated = QtCore.Signal(pm.PyNode)
    def __init__(self, tabSet, parent=None):
        super(LayerWidget, self).__init__(name='Layer', parent=parent)
        self._tabSet = None
        self._layers = []

        self.layerBox = QtWidgets.QComboBox()
        self.layerBox.setMaximumWidth(200)
        self.setField(self.layerBox)
        newLayerButton = QtWidgets.QPushButton('+')
        newLayerButton.setFixedWidth(30)
        self.layout.addWidget(newLayerButton)
        newLayerButton.clicked.connect(self.newLayerDialog)

        self.setTabSet(tabSet)

    def setTabSet(self, tabSet):
        if not isinstance(tabSet, (objSets.TabSet)):
            raise TypeError('tabSet parameter must be a TabSet, got {} instead'.format(type(tabSet)))

        self._tabSet = tabSet
        self._layers = [self._tabSet]

        self.layerBox.clear()
        self.layerBox.addItem('Base')

        for layer in self._tabSet.getLayers():
            self.layerBox.addItem(layer.getTitle())
            self._layers.append(layer)

    def newLayerDialog(self):
        dialog = CreateLayerWidget(parent=self)
        dialog.accepted.connect(lambda: self.newLayer(dialog.getName(), dialog.getTitle(), dialog.getColorNormalizedVector()))
        dialog.exec_()

    @mayaUtils.undoChunk
    def newLayer(self, name, title, color=(.250, .125, .75)):
        layer = self._tabSet.newLayer(name, title, color)
        self.layerBox.addItem(layer.getTitle(), userData=layer)
        self.layerBox.setCurrentIndex(self.layerBox.count() - 1)
        self._layers.append(layer)
        self.layerCreated.emit(layer)

    def getCurrentSet(self):
        return self._layers[self.layerBox.currentIndex()]

    def setCurrentSet(self, objSet):
        if objSet in self._layers:
            idx = self._layers.index(objSet)
            self.layerBox.setCurrentIndex(idx)


# ---- Set List UI ---- #
class SetListWidget(uiUtils.StandardNodeListWidget):
    _EDIT = False
    createRequested = QtCore.Signal()
    visibilityChanged = QtCore.Signal(bool)

    def __init__(self, objSet=None, parent=None):
        super(SetListWidget, self).__init__(parent=parent)

        self.setWindowTitle('Controllers')

        self.listView.customContextMenuRequested.connect(lambda x: self.openMenu(self.listView.mapToGlobal(x)))

        self.objSet = None
        if objSet is not None:
            self.setObjSet(objSet)

        self._deletable = True
        self._closeOnDelete = True

    def sizeHint(self):
        return QtCore.QSize(250, 300)

    def showEvent(self, event):
        super(SetListWidget, self).showEvent(event)
        self.visibilityChanged.emit(True)

    def hideEvent(self, event):
        super(SetListWidget, self).hideEvent(event)
        self.visibilityChanged.emit(False)

    @property
    def deletable(self):
        return self._deletable

    @deletable.setter
    def deletable(self, value):
        self._deletable = value

    @property
    def closeOnDelete(self):
        return self._closeOnDelete

    @closeOnDelete.setter
    def closeOnDelete(self, value):
        self._closeOnDelete = value

    def setEditMode(self, value):
        self._EDIT = value

    def setObjSet(self, objSet):
        if objSet is None:
            self.objSet = None
            self.proxyModel.setSourceModel(QtCore.QAbstractListModel())
            return

        if not isinstance(objSet, pm.nodetypes.ObjectSet):
            raise TypeError('%s is not an ObjectSet' % objSet.name())

        self.objSet = objSet

        # Set Model
        model = SetListModel(objSet)
        self.setModel(model)

    def openMenu(self, pos):
        menu = QtWidgets.QMenu(self)
        if self._EDIT:
            if self.objSet is None:
                createAction = menu.addAction('Create...')
                createAction.triggered.connect(self.createRequested.emit)
            else:
                selectAction = menu.addAction('Select')
                selectAction.triggered.connect(self.selectObjects)
                menu.addSeparator()
                clearAction = menu.addAction('Clear')
                clearAction.triggered.connect(self.clearSet)
                removeAction = menu.addAction('Remove')
                removeAction.triggered.connect(self.removeSelected)
                addAction = menu.addAction('Add selection')
                addAction.triggered.connect(lambda: self.addToSet(pm.ls(sl=True), False))
                replaceAction = menu.addAction('Replace by selection')
                replaceAction.triggered.connect(lambda: self.addToSet(pm.ls(sl=True), True))
                if self._deletable:
                    deleteAction = menu.addAction('Delete')
                    deleteAction.triggered.connect(self.deleteSet)
        else:
            if self.objSet is None:
                return
            else:
                selectAction = menu.addAction('Select')
                selectAction.triggered.connect(self.selectObjects)

        menu.exec_(pos)

    def mousePressEvent(self, event):
        super(SetListWidget, self).mousePressEvent(event)

        if event.button() == QtCore.Qt.RightButton:
            self.openMenu(event.globalPos())

    @mayaUtils.undoChunk
    def clearSet(self):
        pm.sets(self.objSet, e=True, clear=True)
        self.setObjSet(self.objSet)

    @mayaUtils.undoChunk
    def addToSet(self, elements, replace=False):
        if replace:
            self.clearSet()

        for elm in elements:
            if elm not in self.objSet.members():
                _ = pm.sets(self.objSet, e=True, add=elm)

        self.setObjSet(self.objSet)

    @mayaUtils.undoChunk
    def removeSelected(self, confirm=True):
        if confirm:
            dialog = QtWidgets.QMessageBox.critical(self, 'ERMAHGERD !', 'Are you sure you wanna remove these ?',
                                                    QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel,
                                                    QtWidgets.QMessageBox.Cancel)
            if not dialog == QtWidgets.QMessageBox.Ok:
                return
        nodes = self.selectedNodes()

        for node in nodes:
            if node in self.objSet.members():
                _ = pm.sets(self.objSet, e=True, rm=node)

        self.setObjSet(self.objSet)

    @mayaUtils.undoChunk
    def deleteSet(self, confirm=True):
        if confirm:
            dialog = QtWidgets.QMessageBox.critical(self, 'ERMAHGERD !', 'Are you sure you wanna delete this set ?',
                                                    QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel,
                                                    QtWidgets.QMessageBox.Cancel)
            if not dialog == QtWidgets.QMessageBox.Ok:
                return
        pm.delete(self.objSet)
        self.objSet = None
        if self._closeOnDelete:
            self.deleteLater()


class SetListModel(QtCore.QAbstractListModel):
    def __init__(self, objSet, parent=None):
        super(SetListModel, self).__init__(parent)
        self.objSet = objSet
        self.nodes = objSets.getOrderedSetMembers(self.objSet)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.nodes)

    def data(self, index, role):
        if isinstance(index, int):
            row = index
        else:
            row = index.row()

        if role == QtCore.Qt.DisplayRole:
            if self.nodes[row] is None:
                return "None"
            return self.nodes[row].name()

        if role == QtCore.Qt.UserRole:
            return self.nodes[row]

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            return "Controllers"

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


# ---- Space Switch UI ---- #
class SpaceSwitchList(SetListWidget):
    def __init__(self, objSet=None, parent=None):
        super(SpaceSwitchList, self).__init__(objSet, parent)

    def openMenu(self, pos):
        menu = QtWidgets.QMenu(self)
        if self._EDIT:
            if self.objSet is None:
                createAction = menu.addAction('Create...')
                createAction.triggered.connect(self.createRequested.emit)
            else:
                selectAction = menu.addAction('Select')
                selectAction.triggered.connect(self.selectObjects)
                menu.addSeparator()
                clearAction = menu.addAction('Clear')
                clearAction.triggered.connect(self.clearSet)
                removeAction = menu.addAction('Remove')
                removeAction.triggered.connect(self.removeSelected)
                editAction = menu.addAction('Edit...')
                editAction.triggered.connect(self.openEditDialog)
                if self._deletable:
                    deleteAction = menu.addAction('Delete')
                    deleteAction.triggered.connect(self.deleteSet)
        else:
            if self.objSet is None:
                return
            else:
                selectAction = menu.addAction('Select')
                selectAction.triggered.connect(self.selectObjects)

        menu.exec_(pos)

    def openEditDialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        layout = QtWidgets.QVBoxLayout(dialog)

        listView = uiUtils.FilterAttributesListWidget()
        layout.addWidget(listView)

        btn = QtWidgets.QPushButton('Add')
        layout.addWidget(btn)
        btn.clicked.connect(dialog.accept)
        dialog.show()

        dialog.accepted.connect(lambda: self.addToSet(listView.selectedNodes(), False))


class SpaceSwitchWidget(QtWidgets.QWidget):
    _EDIT = False
    createRequested = QtCore.Signal(list)

    def __init__(self, objSet, horizontal=False, parent=None):
        super(SpaceSwitchWidget, self).__init__(parent=parent)

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setAlignment(QtCore.Qt.AlignTop)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0,0,0,0)

        listsWidget = QtWidgets.QWidget(self)
        self._layout.addWidget(listsWidget)

        if horizontal:
            self.listsLayout = QtWidgets.QHBoxLayout(listsWidget)
            self.listsLayout.setAlignment(QtCore.Qt.AlignLeft)
        else:
            self.listsLayout = QtWidgets.QVBoxLayout(listsWidget)
            self.listsLayout.setAlignment(QtCore.Qt.AlignTop)
        self.listsLayout.setSpacing(0)
        self.listsLayout.setContentsMargins(0, 0, 0, 0)

        self.setListWidget = SpaceSwitchList(objSet)
        self.listsLayout.addWidget(self.setListWidget)

        self.enumList = QtWidgets.QListWidget()
        self.listsLayout.addWidget(self.enumList)

        btn = QtWidgets.QPushButton('>>')
        self._layout.addWidget(btn)
        btn.clicked.connect(self.doSwitch)

        self.setListWidget.listView.selectionModel().selectionChanged.connect(self.updateEnumList)
        self.setListWidget.createRequested.connect(self.openCreateDialog)

    def sizeHint(self):
        return QtCore.QSize(250, 250)

    def setEditMode(self, value):
        self._EDIT = value
        self.setListWidget.setEditMode(value)

    def setObjSet(self, objSet):
        self.setListWidget.setObjSet(objSet)
        self.objSet = objSet

    def updateEnumList(self, *args):
        attributes = self.setListWidget.selectedNodes()
        values = []
        for at in attributes:
            enumList = pm.attributeQuery(at.longName(), node=at.node(), listEnum=True)
            if enumList is None:
                continue
            enumList = enumList[0].split(':')
            values.append(enumList)

        values = list(set(values[0]).intersection(*values))

        self.enumList.clear()
        self.enumList.addItems(values)

    def openCreateDialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        layout = QtWidgets.QVBoxLayout(dialog)

        listView = uiUtils.FilterAttributesListWidget()
        layout.addWidget(listView)

        btn = QtWidgets.QPushButton('Create')
        layout.addWidget(btn)
        btn.clicked.connect(dialog.accept)
        dialog.show()

        dialog.accepted.connect(lambda :self.createRequested.emit(listView.selectedNodes()))

    @mayaUtils.undoChunk
    def doSwitch(self):
        selEnums = self.enumList.selectedItems()
        if not len(selEnums):
            return

        spaceName = selEnums[0].text()
        for at in self.setListWidget.selectedNodes():
            node = at.node()
            enumList = pm.attributeQuery(at.longName(), node=at.node(), listEnum=True)
            enumList = enumList[0].split(':')

            idx = enumList.index(spaceName)     # Find the index of the selected space

            mtx = node.worldMatrix.get()        # Get current world matrix
            at.set(idx)     # Change the space

            mtx = mtx * node.parentInverseMatrix.get()       # Convert the world matrix to current local space

            # Decompose the matrix
            mtx = dt.TransformationMatrix(mtx)
            translate = mtx.translate
            rotate = mtx.euler
            scale = mtx.scale

            ro = ['XYZ', 'YZX', 'ZXY', 'XZY', 'YXZ', 'ZYX'][node.rotateOrder.get()]
            rotate.reorderIt(ro)
            rotate.setDisplayUnit('degrees')

            values = {'translateX': translate.x,
                      'translateY': translate.y,
                      'translateZ': translate.z,
                      'rotateX': rotate.x,
                      'rotateY': rotate.y,
                      'rotateZ': rotate.z,
                      'scaleX': scale.x,
                      'scaleY': scale.y,
                      'scaleZ': scale.z}

            for trsf in ('translate', 'rotate', 'scale'):
                for axis in ['X', 'Y', 'Z']:
                    try:
                        atName = trsf + axis
                        node.attr(atName).set(values[atName])
                    except:
                        pass


# ---- Export / Import ---- #
def exportObjectSetDialog(node, parent=None):
    if not isinstance(node, objSets.MasterSet):
        raise TypeError('Can\'t Export that shit. Lol.')

    data = node.getData()
    path = QtWidgets.QFileDialog.getSaveFileName(parent,
                                                 'Export', os.path.dirname(__file__),
                                                 "Picker Files (*.pkr)")
    if not len(path[0]):
        return None

    with open(path[0], 'w') as outFile:
        outFile.write(json.dumps(data))
        sys.stdout.write('Exporting to : {}'.format(path[0]))

    return outFile


class ImportObjectSetDialog(QtWidgets.QDialog):
    winName = 'import_object_set'
    winTitle = 'Import Object Set'
    setCreated = QtCore.Signal(objSets.BaseSet)

    def __init__(self, parent=None):
        mayaMainWindow = getMayaWindow()

        # check if window already exists:
        for win in mayaMainWindow.findChildren(QtWidgets.QWidget, self.winName):
            win.close()

        super(ImportObjectSetDialog, self).__init__(parent=parent)
        self.setWindowTitle(self.winTitle)
        self.setObjectName(self.winName)
        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setAlignment(QtCore.Qt.AlignTop)
        self._layout.setSpacing(10)

        fromWidget = uiUtils.LabeledField('Replace')
        self.fromField = QtWidgets.QLineEdit()
        fromWidget.setField(self.fromField)
        self._layout.addWidget(fromWidget)

        toWidget = uiUtils.LabeledField('With')
        self.toField = QtWidgets.QLineEdit()
        toWidget.setField(self.toField)
        self._layout.addWidget(toWidget)

        fileWidget = uiUtils.LabeledField('File')
        self.fileField = QtWidgets.QLineEdit()
        self.fileField.setMinimumWidth(200)
        fileWidget.setField(self.fileField)
        self._layout.addWidget(fileWidget)
        openBtn = QtWidgets.QPushButton('Open')
        fileWidget.layout.addWidget(openBtn)
        openBtn.clicked.connect(self.openFileDialog)

        # ----- Buttons ----- #
        btnLayout = QtWidgets.QHBoxLayout(self)
        self._layout.addLayout(btnLayout)
        btnLayout.setAlignment(QtCore.Qt.AlignCenter)
        btnLayout.setContentsMargins(0, 0, 0, 0)

        importBtn = QtWidgets.QPushButton('Import')
        btnLayout.addWidget(importBtn)
        importBtn.clicked.connect(self.accept)

        cancelBtn = QtWidgets.QPushButton('Cancel')
        btnLayout.addWidget(cancelBtn)
        cancelBtn.clicked.connect(self.close)

        self.fileField.textChanged.connect(lambda x: importBtn.setEnabled(True if len(self.fileField.text()) else False))

    def openFileDialog(self):
        path = QtWidgets.QFileDialog.getOpenFileName(self,
                                                     'Import', os.path.dirname(__file__),
                                                     "Picker Files (*.pkr)")
        self.fileField.setText(path[0])

    def doImport(self):
        path = self.fileField.text()

        if not len(path):
            return None
        with open(path) as inFile:
            data = json.load(inFile)
            sys.stdout.write('Importing file : {}'.format(path))

        return data

    def accept(self):
        result = self.doImport()
        if result is not None:
            self.accepted.emit()
            self.close()


class ImportMasterSetDialog(ImportObjectSetDialog):
    winName = 'import_master_set'
    winTitle = 'Import UI'

    def __init__(self, parent=None):
        super(ImportMasterSetDialog, self).__init__(parent=parent)

    def doImport(self):
        data = super(ImportMasterSetDialog, self).doImport()
        if data is None:
            return None

        mSet = objSets.MasterSet.createFromData(data, searchAndReplace=(self.fromField.text(), self.toField.text()))
        self.setCreated.emit(mSet)
        return data


def dockWidget(widget, width=600):
    name = widget.objectName() + '_dock'
    title = widget.windowTitle()
    try:
        cmds.deleteUI(name)
    except RuntimeError:
        pass

    dockControl = cmds.workspaceControl(
        name,
        tabToControl=["ToolSettings", -1],
        initialWidth=width,
        minimumWidth=True,
        widthProperty="preferred",
        label=title
    )

    dockPtr = mui.MQtUtil.findControl(dockControl)
    dockWidget = wrapInstance(int(dockPtr), QtWidgets.QWidget)
    dockWidget.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    dockWidget.layout().addWidget(widget)

    cmds.evalDeferred(
        lambda *args: cmds.workspaceControl(
            dockControl,
            edit=True,
            restore=True
        )
    )

    return dockWidget