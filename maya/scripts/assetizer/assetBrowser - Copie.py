
"""
import sys
sys.path.append("D:/gabriel/assetizer/scripts")

import assetBrowser
import importlib
importlib.reload(assetBrowser)

"""


import os
import json
from maya import OpenMaya
from maya import OpenMayaUI as omui
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui
from shiboken2 import wrapInstance
from pathlib import Path
import shutil
import subprocess
import time
from datetime import datetime

#TO DO: packageClass()
#CONNECT BUTTON

def maya_main_window():
    '''
    Return the Maya main window widget as a Python object
    '''
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)




current_project = "B:/trashtown_2112"
empty_scene = ""
all_assets_dir = os.path.join(current_project,"assets")
all_shots_dir =  os.path.join(current_project,"shots")

template_directories = {"assets" :["modeling","shading","rigging"],
                        "shots" : ["anim","lighting","comp"]
                        }

maya_taks_template = ["modeling","shading","rigging","publish","anim","lighting"]


def copy2clip(txt):
    cmd='echo '+txt.strip()+'|clip'
    return subprocess.check_call(cmd, shell=True)

def convert_to_octet(size):
    """ Convert bytes to KB, or MB or GB"""
    for x in ['bit', 'Ko', 'Mo', 'Go', 'To']:
        if size < 1024.0:
            return "%3.0f %s" % (size, x)
        size /= 1024.0

blackList_start_name = ["."]
blackList_end_name = [".db"]
def not_blacklisted(name):
    """ check if the name has illegal start or end characters """
    state = True
    for x in blackList_start_name:
        if name.startswith(x) or name.endswith(x) :
            state = False
    return state


def list_set_selected_byName(list,name):
    """
    Try to select an item from a list matching a name.
    If there is no match then select first row.
    """
    # DIRTY HACK TO PRESELECT SHADING_LIB IF PUBLISH DIRECTORY DOES NOT EXIST ELSE SELECT PUBLISH
    list_item = [list.item(x).text() for x in range(list.count())]
    for item in list_item:
        if "shading_lib" in item and "publish" not in list_item:
            name = item
    #DIRTY HACK END #

    items = list.findItems(name,QtCore.Qt.MatchExactly)
    list.setCurrentItem(items[0]) if len(items)>0 else list.setCurrentRow(0)


class Package():
    def __init__(self, name, type):
        self.name = name
        type_dir = "assets" if type == "asset" else "shots"
        self.favorite_dir = "publish" if type == "asset" else "lighting"
        dir = os.path.join(current_project,type_dir,name)
        self.dir = dir if os.path.isdir(dir) else None
        self.shading_scene = None



class AssetBrowser(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(AssetBrowser, self).__init__(parent)
        self.qtSignal = QtCore.Signal()

        #################################################################
    def create(self):
        self.setWindowTitle("AssetBrowser")
        self.setWindowFlags(QtCore.Qt.Tool)
        self.resize(950, 400) # re-size the window


        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.comboLayout = QtWidgets.QHBoxLayout(self)
        self.rightLayout = QtWidgets.QVBoxLayout(self)
        self.topLayout = QtWidgets.QHBoxLayout(self)
        self.bodyLayout = QtWidgets.QHBoxLayout(self)

        #WIDGET BUTTONS
        self.buttons_layout =  QtWidgets.QHBoxLayout(self)
        self.buttons_left_layout = QtWidgets.QVBoxLayout(self)
        self.buttons_right_layout = QtWidgets.QVBoxLayout(self)

        #WIDGET QPushButton
        self.button_mode_asset = QtWidgets.QPushButton("Asset")
        self.button_mode_asset.setCheckable(True)
        self.button_mode_asset.setMaximumWidth(130)
        self.button_mode_shot = QtWidgets.QPushButton("Shot")
        self.button_mode_shot.setCheckable(True)
        self.button_mode_shot.setMaximumWidth(130)

        #Add New item buttons
        self.button_add_new = QtWidgets.QPushButton("Create new")

        # WIDGET LIST
        self.package_Qlist = QtWidgets.QListWidget()
        self.package_Qlist.setMaximumWidth(200)
        self.package_Qlist.setMinimumWidth(160)

        self.second_Qlist = QtWidgets.QListWidget()
        self.second_Qlist.setMaximumWidth(220)
        self.second_Qlist.setMinimumWidth(160)

        self.third_Qlist = QtWidgets.QListWidget()

        #WIDGET CHECKBOX
        self.use_latest =  QtWidgets.QCheckBox("Use latest version")
        self.use_latest.setChecked(True)


        self.display_label = QtWidgets.QLabel("Asset:")
        self.import_button = QtWidgets.QPushButton("Import")
        self.reference_button = QtWidgets.QPushButton("Reference")
        self.open_folder = QtWidgets.QPushButton("Open folder")
        self.open_scene = QtWidgets.QPushButton("Open scene")
        self.copy_path = QtWidgets.QPushButton("Copy path")

        #DISPLAY IMAGE

        imgPath = ""
        self.image = QtGui.QImage(imgPath)
        self.pixmap = QtGui.QPixmap(self.image.scaledToWidth(450))



        self.label = QtWidgets.QLabel()
        self.label.setPixmap(self.pixmap)

        self.package_infos_label =  QtWidgets.QLabel()




        #self.resize(pixmap.width(), pixmap.height())
        # ADD WIDGET TO LAYOUT

        self.comboLayout.addWidget(self.package_Qlist)

        self.comboLayout.addWidget(self.second_Qlist)
        self.comboLayout.addWidget(self.third_Qlist)

        self.rightLayout.addWidget(self.label)
        self.rightLayout.addStretch()
        self.rightLayout.addWidget(self.package_infos_label)
        self.rightLayout.addLayout(self.buttons_layout)



        #self.buttons_left_layout.addWidget(self.use_latest)
        #self.buttons_left_layout.addWidget(self.display_label)
        self.buttons_left_layout.addStretch()
        self.buttons_left_layout.addWidget(self.import_button)
        self.buttons_left_layout.addWidget(self.reference_button)
        self.buttons_left_layout.addWidget(self.open_scene)
        self.buttons_right_layout.addStretch()
        self.buttons_right_layout.addWidget(self.open_folder)
        self.buttons_right_layout.addWidget(self.copy_path)
        #self.buttons_right_layout.addStretch()
        #self.buttons_layout.addWidget(self.copy_path)


        self.buttons_layout.addLayout(self.buttons_left_layout)
        self.buttons_layout.addLayout(self.buttons_right_layout)

        self.bodyLayout.addLayout(self.comboLayout)
        self.bodyLayout.addLayout(self.rightLayout)

        self.topLayout.addWidget(self.button_mode_asset)
        self.topLayout.addWidget(self.button_mode_shot)
        self.topLayout.addWidget(self.button_add_new)
        self.topLayout.addStretch()
        self.mainLayout.addLayout(self.topLayout)
        self.mainLayout.addLayout(self.bodyLayout)

        #OPEN BY DEFAULT AS ASSET BROWSER
        self.button_mode_asset.setChecked(True)
        self.mode = "asset"
        self.all_packages_dir = os.path.join(current_project,"assets")
        self.rebuild_package_list()
        self.package_Qlist.setCurrentRow(0)
        self.package_Qlist_changed()

        #CONNECT WIDGET
        self.import_button.clicked.connect(self.import_clicked)
        self.open_folder.clicked.connect(self.open_folder_clicked)
        self.open_scene.clicked.connect(self.open_scene_clicked)
        self.copy_path.clicked.connect(self.copy_path_clicked)
        #Connect asset and shot buttons
        self.button_mode_asset.clicked.connect(self.button_mode_asset_clicked)
        self.button_mode_shot.clicked.connect(self.button_mode_shot_clicked)
        self.button_add_new.clicked.connect(self.button_add_new_clicked)

        self.reference_button.clicked.connect(self.reference_clicked)
        self.package_Qlist.itemClicked.connect(self.package_Qlist_changed)
        self.second_Qlist.itemClicked.connect(self.second_Qlist_changed)
        self.third_Qlist.itemClicked.connect(self.third_Qlist_changed)
        #self.second_Qlist.itemClicked.connect(self.second_Qlist_changed)
        #self.use_latest.stateChanged.connect(self.use_latest_changed)

    #### QLIST CHANGED ####
    def package_Qlist_changed(self):
        """When in mode "Shot": rebuild the departement list (lighting, animation, etc.)
           When in mode "Asset": rebuild the shading list
        """

        packageName = self.package_Qlist.currentItem().text()
        self.package = Package(packageName, self.mode)
        if self.package.dir is not None:
            self.rebuild_departementList()
            self.rebuild_files_list()
            self.rebuild_image()

    def second_Qlist_changed(self):
        self.rebuild_files_list()

    def third_Qlist_changed(self):
        path, namespace = self.build_path_scene()
        metadata = self.get_file_metadata(path)
        self.package_infos_label.setText(metadata)
    #### REBUILD LIST ####

    def rebuild_package_list(self):
        self.clear_all_list()
        packages_list = os.listdir(self.all_packages_dir)
        for package in packages_list:
            self.package_Qlist.addItem(package)

    ## SHOT MODE ##
    def rebuild_departementList(self):
        """ List all the departements of the current selected shot"""
        list = os.listdir(self.package.dir)
        self.second_Qlist.clear()
        for file in list:
            self.second_Qlist.addItem(file)

        list_set_selected_byName(self.second_Qlist,self.package.favorite_dir)

    def rebuild_files_list(self):
        departement_dir = os.path.join(self.package.dir,self.second_Qlist.currentItem().text())
        list = os.listdir(departement_dir) if os.path.isdir(departement_dir)  else []
        list.sort()
        list.reverse()
        self.third_Qlist.clear()
        for file in list:
            self.third_Qlist.addItem(file)
        self.third_Qlist.setCurrentRow(0)
        self.third_Qlist_changed()


    ## ASSET MODE ##

    def rebuild_image(self):
        list = os.listdir(self.package.dir)
        preview_image_list = [file for file in list if file.lower().endswith(('.png', '.jpg', '.jpeg' ))]
        if len(preview_image_list) > 0:
            preview_image_path = os.path.join(self.package.dir,preview_image_list[-1])
        else:
            absolute_path = os.path.dirname(os.path.realpath(__file__))
            preview_image_path = os.path.join(absolute_path, "icons","no_preview.png")

        self.image = QtGui.QImage(preview_image_path)

        self.pixmap = QtGui.QPixmap(self.image.scaledToWidth(450))
        self.label.setPixmap(self.pixmap)

    def get_file_metadata(self, file_path):
        #size = os.path.getsize(file_path)
        #last_modified = os.path.getmtime(file_path)
        modificationTime = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')

        size = os.path.getsize(file_path)
        octet_size = convert_to_octet(size)

        metadatas = "Size: %s - Last modified: %s"%(octet_size  ,modificationTime  )
        return metadatas





    ### UTILITY FUNCTION  ###
    def clear_all_list(self):
        self.package_Qlist.clear()
        self.second_Qlist.clear()
        self.third_Qlist.clear()

    ### BUTTON CLICKED ###

    def button_add_new_clicked(self):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog',
            'Name:')

        if ok:
            self.create_entity(str(text))

    def create_entity(self, name):
        mode = "assets" if self.button_mode_asset.isChecked() else "shots"
        path = os.path.join(current_project,mode,name)
        template_directory = template_directories[mode]
        for task in template_directory:
            task_dir = os.path.join(path,task)
            os.makedirs(task_dir, exist_ok=True)

            #SKIPE DEFAULT SCENE CREATION IN NOT A MAYA TYPE
            if task not in maya_taks_template:
                continue

            task_file = os.path.join(task_dir,name+"_"+task+".0000.ma")
            if not os.path.isfile(task_file):
                absolute_path = os.path.dirname(os.path.realpath(__file__))
                scene_empty = os.path.join(absolute_path, "template","empty.ma")
                shutil.copy(scene_empty,task_file)

        self.rebuild_package_list()

    def button_mode_asset_clicked(self):
        if self.button_mode_asset.isChecked() and self.button_mode_shot.isChecked() ==True:
            self.mode = "asset"
            self.all_packages_dir = os.path.join(current_project,"assets")
            self.rebuild_package_list()
            self.button_mode_shot.setChecked(False)
        else:
            self.button_mode_asset.setChecked(True)
            pass

    def button_mode_shot_clicked(self):
        if self.button_mode_shot.isChecked() and self.button_mode_asset.isChecked() ==True:
            self.mode = "shot"
            self.all_packages_dir = os.path.join(current_project,"shots")
            self.rebuild_package_list()
            self.third_Qlist.setVisible(True)
            self.button_mode_asset.setChecked(False)
        else:
            self.button_mode_shot.setChecked(True)
            pass

    def build_path_scene(self):
        package_name = self.package_Qlist.currentItem().text()
        package_departement = self.second_Qlist.currentItem().text()
        departement_path = os.path.join(self.package.dir, package_departement)
        if os.path.isfile(departement_path):
            path = departement_path
            namespace = os.path.splitext(package_departement)[0]
        else:
            package_scene = self.third_Qlist.currentItem().text()
            namespace = os.path.splitext(package_scene)[0]
            path = os.path.join(self.package.dir,package_departement,package_scene)
        return path, namespace

    def import_clicked(self):
        path, namespace = self.build_path_scene()
        cmds.file(path, i=True, namespace=namespace)

    def reference_clicked(self):
        path, namespace = self.build_path_scene()
        cmds.file(path, reference=True,namespace=namespace)

    def open_folder_clicked(self):
        os.startfile(self.package.dir)

    def copy_path_clicked(self):
        path, namespace = self.build_path_scene()
        copy2clip(path)

    def open_scene_clicked(self):
        path, namespace = self.build_path_scene()
        cmds.file(path, open=True, force=True)


try:

    ui.deleteLater()
except:
    pass
ui = AssetBrowser()
ui.create()
ui.show()
