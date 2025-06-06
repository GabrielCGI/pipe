from functools import partial
import maya.cmds as cmds
# Retrieve the version of Maya currently in use
maya_version = cmds.about(version=True)

if maya_version.startswith("2022"):
    # Using PySide2 for Maya 2022
    from PySide2 import QtCore, QtWidgets, QtGui
elif maya_version.startswith("2025"):
    # Using PySide6 for Maya 2025
    # Note: QAction and QShortcut have moved from QtWidgets to QtGui in PySide6
    from PySide6 import QtCore, QtWidgets, QtGui


import gf_animUI.setup as animUI
from gf_animtools.tools import mirrorCtr, setDynamicValue
from gf_animtools.rig.mods.at_limbs_mod import LimbsGroup, QLimbsGroup


class ExtendedDockedAnimWindow(animUI.ui.DockedAnimWindow):
    def __init__(self, masterSet, showEditToolBar=False):
        super(ExtendedDockedAnimWindow, self).__init__(masterSet=masterSet, showEditToolBar=showEditToolBar)
        customizeAnimWindow(self)


class ExtendedAnimWindow(animUI.ui.AnimWindow):
    def __init__(self, masterSet, showEditToolBar=False):
        super(ExtendedAnimWindow, self).__init__(masterSet=masterSet, showEditToolBar=showEditToolBar)
        self.toolsDockWidget = None
        self.initToolsWidget()
        customizeAnimWindow(self)
        self._updatePickersTabSize()

    def initToolsWidget(self):
        if self.toolsWidget is None:
            self.toolsWidget = QtWidgets.QSplitter(QtCore.Qt.Vertical, parent=self)
            self.toolsDockWidget = QtWidgets.QDockWidget()
            self.toolsDockWidget.setWindowTitle('Tools')
            self.toolsDockWidget.setWidget(self.toolsWidget)
            self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.toolsDockWidget)
        return self.toolsWidget


def customizeAnimWindow(window):
    # ----- Custom Tools widget ----- #
    namespace = window._masterSet.namespace()
    limbs_modules = LimbsGroup.list('{}*'.format(namespace))
    limbs_modules.extend(QLimbsGroup.list('{}*'.format(namespace)))
    window.ikfkWidget = IKFKSwitchWidget(mods=limbs_modules)
    window.toolsWidget.addWidget(window.ikfkWidget)

    # ----- Custom Toolbar ----- #
    window.initCustomToolBar()
    window.mirrorAction = window.customToolBar.addAction('Mirror')
    window.mirrorAction.triggered.connect(mirrorCtr)

    window.dynamicOnAction = window.customToolBar.addAction('Dyn ON')
    window.dynamicOnAction.triggered.connect(partial(setDynamicValue, True))
    window.dynamicOnAction = window.customToolBar.addAction('OFF')
    window.dynamicOnAction.triggered.connect(partial(setDynamicValue, False))


class IKFKSwitchWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, mods=None):
        if mods is None:
            raise TypeError('Must provide a list of limbs modules')

        super(IKFKSwitchWidget, self).__init__(parent=parent)
        self.mods = mods

        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self.rightWidget = QtWidgets.QWidget(self)
        self.rightLayout = QtWidgets.QVBoxLayout(self.rightWidget)
        self.rightLayout.setSpacing(0)
        self.rightLayout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.rightWidget)

        self.centerWidget = QtWidgets.QWidget(self)
        self.centerLayout = QtWidgets.QVBoxLayout(self.centerWidget)
        self.centerLayout.setSpacing(0)
        self.centerLayout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.centerWidget)

        self.leftWidget = QtWidgets.QWidget(self)
        self.leftLayout = QtWidgets.QVBoxLayout(self.leftWidget)
        self.leftLayout.setSpacing(0)
        self.leftLayout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.leftWidget)

        for mod in self.mods:
            if mod.mod_suffix.endswith('_L'):
                layout = self.leftLayout
            elif mod.mod_suffix.endswith('_R'):
                layout = self.rightLayout
            else:
                layout = self.centerLayout

            btn = QtWidgets.QPushButton('{}{}'.format(mod.mod_name, mod.mod_suffix))
            btn.clicked.connect(mod.ikFkSwitch)
            btn.setFixedHeight(35)
            layout.addWidget(btn)