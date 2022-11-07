
"""
import sys
sys.path.append("D:/gabriel/assetizer/scripts")

import assetLoader
import importlib
importlib.reload(assetLoader)

"""

#TO DO ADD LOD AND VARIANT DROPDOWN

from maya import OpenMayaUI as omui
import os
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import asset as assetTool
import importlib
importlib.reload(assetTool)


def maya_main_window():
    '''
    Return the Maya main window widget as a Python object
    '''
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)



class AssetLoader(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(AssetLoader, self).__init__(parent)
        self.qtSignal = QtCore.Signal()
        #################################################################
    def create(self):
        self.setWindowTitle("AssetLoader")
        self.setWindowFlags(QtCore.Qt.Tool)
        self.resize(300, 100) # re-size the window

        # LAYOUT
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.comboLayout = QtWidgets.QHBoxLayout(self)

        # WIDGET
        self.variant_ComboBox = QtWidgets.QComboBox()
        self.variantSet_ComboBox = QtWidgets.QComboBox()
        self.display_label = QtWidgets.QLabel("")
        self.load_asset_button = QtWidgets.QPushButton("Select asset")

        # ADD WIDGET TO LAYOUT
        self.mainLayout.addLayout(self.comboLayout)
        self.comboLayout.addWidget(self.variant_ComboBox)
        self.comboLayout.addWidget(self.variantSet_ComboBox)
        self.mainLayout.addWidget(self.load_asset_button)
        self.mainLayout.addWidget(self.display_label)

        #CONNECT WIDGET
        self.load_asset_button.clicked.connect(self.load_asset_clicked)
        self.variantSet_ComboBox.activated.connect(self.variantSet_ComboBox_changed)
        self.variant_ComboBox.activated.connect(self.variant_ComboBox_changed)

    def load_asset_clicked(self):
        #GET PRoXY NAME FROM MAYA SELECTION
        debug = 1
        maya_proxy_name = cmds.ls(selection=True)[0]
        if debug == 1: print ("BEGGING... "+ maya_proxy_name)
        #BUILD ASSET OBJECT FROM PROXY NAME
        self.asset = assetTool.Asset(maya_proxy_name)



        #CLEAR COMBOBOX
        self.variant_ComboBox.clear()
        self.variantSet_ComboBox.clear()


        #Set variantSets combobox
        for variantSet in self.asset.all_variantSets:
            self.variantSet_ComboBox.addItem(variantSet.name)

        self.variantSet_ComboBox.setCurrentText(self.asset.current_variantSetName)

        #Build variant combo box
        self.rebuild_variant_ComboBox()

    def rebuild_variant_ComboBox(self):
        self.variant_ComboBox.clear()
        variantSetName = self.variantSet_ComboBox.currentText()
        variantSet = self.asset.get_variantSet_by_name(variantSetName)
        print(variantSet.name)
        for variant in variantSet.all_variants:
            pretty_name = variant.name.split(".ass")[0]
            self.variant_ComboBox.addItem(pretty_name)

    def variantSet_ComboBox_changed(self):
        self.rebuild_variant_ComboBox()


    def variant_ComboBox_changed(self):
        selected_variant_name = self.variant_ComboBox.currentText()+".ass"
        selected_variantSet_name = self.variantSet_ComboBox.currentText()
        selected_variant = self.asset.get_variant_by_name(selected_variantSet_name ,selected_variant_name)
        print(selected_variant.name)
        print(selected_variant.full_path)
        new_dso = selected_variant.full_path
        cmds.setAttr(self.asset.maya_proxy_name+".dso", new_dso, type="string")
        self.display_label.setText(new_dso)






try:
    ui.deleteLater()
except:
    pass
ui = AssetLoader()
ui.create()
ui.show()
