
from maya import OpenMayaUI as omui
import os
import json
from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance
from pathlib import Path
import sys
import assetPublisher_pymel as pub
import utils_pymel as utils
import importlib
importlib.reload(pub)
importlib.reload(utils)
import pymel.core as pm


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
        self.button_layout = QtWidgets.QVBoxLayout(self)
        self.checkbox_layout = QtWidgets.QHBoxLayout(self)


        # WIDGET LIST


        #WIDGET CHECKBOX
        self.is_a_shot_asset =  QtWidgets.QCheckBox("Next to scene")
        self.delete_after_publish =  QtWidgets.QCheckBox("Delete source")
        self.import_published =  QtWidgets.QCheckBox("Import published ")
        self.init_checkbox()


        #self.display_label = QtWidgets.QLabel("Shot mode")
        self.publish_asset = QtWidgets.QPushButton("Publish selected asset")
        self.publish_variant = QtWidgets.QPushButton("Publish selected variant")
        self.set_version = QtWidgets.QPushButton("Set version")


        # ADD WIDGET TO LAYOUT
        #self.checkbox_layout.addWidget(self.display_label)

        self.checkbox_layout.addWidget(self.delete_after_publish)
        self.checkbox_layout.addWidget(self.is_a_shot_asset)
        self.checkbox_layout.addWidget(self.import_published)
        self.checkbox_layout.addStretch()




        self.button_layout.addWidget(self.publish_asset)
        self.button_layout.addWidget(self.publish_variant )
        #self.button_layout.addWidget(self.display_label)


        self.mainLayout.addLayout(self.button_layout)
        self.mainLayout.addLayout(self.checkbox_layout)


        #CONNECT WIDGET
        self.publish_asset.clicked.connect(self.publish_asset_clicked)
        self.publish_variant.clicked.connect(self.publish_variant_clicked)

    def init_checkbox(self):
        filepath = pm.system.sceneName()
        if filepath:
            split = filepath.split("/")
            if "assets" not in split:
                self.delete_after_publish.setChecked(True)
                self.is_a_shot_asset.setChecked(True)
                self.import_published.setChecked(True)

    def publish_asset_clicked(self):
        pub.ask_save()
        maya_root = pm.ls(sl=True)[0]
        asset_dir = self.get_dir()
        pub.publish(maya_root,asset_dir,self.import_published.isChecked())
        if self.delete_after_publish.isChecked():
            pub.deleteSource(maya_root)

    def publish_variant_clicked(self):
        pub.ask_save()
        selected_variant = pm.ls(sl=True)[0]
        maya_root = selected_variant.getParent()
        if not maya_root: utils.warning("Can't get parent")
        asset_dir = self.get_dir()
        pub.publish(maya_root,asset_dir,self.import_published.isChecked(),selected_variant)
        if self.delete_after_publish.isChecked():
            pub.deleteSource(maya_root)



    def get_dir(self):
        if self.is_a_shot_asset.isChecked():
            filepath = pm.system.sceneName()
            asset_dir =os.path.join(os.path.dirname(filepath),"assets")
        else:
            asset_dir = utils.get_working_directory()
        return asset_dir
try:
    ui.deleteLater()
except:
    pass
ui = AssetLoader()
ui.create()
ui.show()
