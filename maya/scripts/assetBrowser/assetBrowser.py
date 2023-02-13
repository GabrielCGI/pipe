
"""
import sys
sys.path.append("D:/gabriel/assetizer/scripts")

import assetBrowser
import importlib
importlib.reload(assetBrowser)

"""

# ######################################################################################################################

_FILE_NAME_PREFS = "asset_browser"

# ######################################################################################################################

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
import fnmatch
from Prefs import Prefs
#TO DO: packageClass()
#CONNECT BUTTON

asset_browser_prefs = Prefs(_FILE_NAME_PREFS)

def maya_main_window():
    '''
    Return the Maya main window widget as a Python object
    '''
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)



#current_project="D:/gabriel/assetizer"
project_list = ["B:/trashtown_2112","I:/battlestar_2206","D:/"]

empty_scene = ""


template_directories = {"assets" :["modeling","shading","rigging"],
                        "shots" : ["anim","lighting","comp"]
                        }

maya_taks_template = ["modeling","shading","rigging","publish","anim","lighting"]
file_color_item = QtGui.QColor(200,200,255)

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
        if name.startswith(x):
            state = False
    for x in blackList_end_name:
        if name.endswith(x):
            state = False
    return state

def list_files_and_dirs_sorted(path, sort_by_last=False):
        file_list =[]
        dir_list= []
        all_list = []
        if not path:
            return file_list, dir_list
        if not os.path.isdir(path):
            return file_list, dir_list

        list = os.listdir(path)
        for x in list:
            if not_blacklisted(x):
                if os.path.isdir(os.path.join(path,x)):
                    dir_list.append(x)
                else:
                    file_list.append(x)
        file_list.sort()
        file_list.reverse()

        if sort_by_last ==True:
            file_list = sorted(file_list, key = lambda x: os.path.getmtime(os.path.join(path,x)))
            file_list.reverse()

        dir_list.sort()
        dir_list.reverse()
        return file_list, dir_list

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
    def __init__(self, name, type, current_project):
        self.name = name

        self.favorite_dir = "publish" if type == "asset" else "lighting"
        dir = os.path.join(current_project,type,name)
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

        self.packageLayout = QtWidgets.QVBoxLayout(self)
        self.departementLayout = QtWidgets.QVBoxLayout(self)
        self.fileLayout = QtWidgets.QVBoxLayout(self)
        self.header_fileLayout = QtWidgets.QHBoxLayout(self)

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
        self.button_add_new = QtWidgets.QPushButton("+")
        self.button_add_new.setMaximumWidth(25)

        #Current prod:
        self.comboBox_current_prod = QtWidgets.QComboBox()
        self.comboBox_current_prod.addItems(project_list)
        #Add Last Modified sort checkbox
        self.sort_by_last_checkbox = QtWidgets.QCheckBox("Sort by last modified")
        self.button_return_previous = QtWidgets.QPushButton("<")
        self.button_return_previous.setMaximumWidth(25)

        # WIDGET LIST
        self.package_Qlist = QtWidgets.QListWidget()
        self.package_Qlist.setMaximumWidth(200)
        self.package_Qlist.setMinimumWidth(160)

        self.second_Qlist = QtWidgets.QListWidget()
        self.second_Qlist_refresh = True
        self.second_Qlist.setMaximumWidth(220)
        self.second_Qlist.setMinimumWidth(160)

        self.third_Qlist = QtWidgets.QListWidget()
        self.third_Qlist.setMinimumWidth(220)

        #WIDGET CHECKBOX
        self.filter_text = QtWidgets.QLineEdit()
        self.filter_text.setMaximumWidth(200)
        self.filter_text.setMinimumWidth(160)
        self.filter_departement = QtWidgets.QLineEdit()
        self.filter_departement.setMaximumWidth(200)
        self.filter_departement.setMinimumWidth(160)



        self.display_label = QtWidgets.QLabel("Asset:")
        self.import_button = QtWidgets.QPushButton("Import")
        self.reference_button = QtWidgets.QPushButton("Reference")
        self.open_folder = QtWidgets.QPushButton("Open folder")
        self.open_scene = QtWidgets.QPushButton("Open scene")
        self.copy_path = QtWidgets.QPushButton("Copy path")

        #DISPLAY IMAGE

        imgPath = "R:/pipeline/pipe/maya/scripts/assetBrowser/icons/open.JPG"
        self.image = QtGui.QImage(imgPath)
        self.pixmap = QtGui.QPixmap(self.image.scaledToWidth(450))

        self.label = QtWidgets.QLabel()
        self.label.setPixmap(self.pixmap)

        self.package_infos_label =  QtWidgets.QLabel()

        # ADD WIDGET TO LAYOUT
        self.packageLayout.addWidget(self.filter_text)
        self.packageLayout.addWidget(self.package_Qlist)

        self.departementLayout.addWidget(self.filter_departement)
        self.departementLayout.addWidget(self.second_Qlist)

        self.header_fileLayout.addWidget(self.button_return_previous)
        self.header_fileLayout.addWidget(self.sort_by_last_checkbox)

        self.fileLayout.addLayout(self.header_fileLayout)

        self.fileLayout.addWidget(self.third_Qlist)

        self.comboLayout.addLayout(self.packageLayout)
        self.comboLayout.addLayout(self.departementLayout)
        self.comboLayout.addLayout(self.fileLayout)



        self.rightLayout.addWidget(self.label)
        self.rightLayout.addWidget(self.package_infos_label)
        self.rightLayout.addStretch()
        self.rightLayout.addLayout(self.buttons_layout)



        self.buttons_left_layout.addStretch()
        self.buttons_left_layout.addWidget(self.import_button)
        self.buttons_left_layout.addWidget(self.reference_button)
        self.buttons_left_layout.addWidget(self.open_scene)
        self.buttons_right_layout.addStretch()
        self.buttons_right_layout.addWidget(self.open_folder)
        self.buttons_right_layout.addWidget(self.copy_path)


        self.buttons_layout.addLayout(self.buttons_left_layout)
        self.buttons_layout.addLayout(self.buttons_right_layout)

        self.bodyLayout.addLayout(self.comboLayout)
        self.bodyLayout.addLayout(self.rightLayout)

        self.topLayout.addWidget(self.button_mode_asset)
        self.topLayout.addWidget(self.button_mode_shot)
        self.topLayout.addWidget(self.button_add_new)
        self.topLayout.addWidget(self.comboBox_current_prod)
        #self.topLayout.addWidget(self.sort_by_last_checkbox)
        #self.topLayout.addWidget(self.filter_text)
        self.topLayout.addStretch()
        self.mainLayout.addLayout(self.topLayout)
        self.mainLayout.addLayout(self.bodyLayout)

        #OPEN BY DEFAULT AS ASSET BROWSER
        if "current_project" in asset_browser_prefs:
            current_project_dir = asset_browser_prefs["current_project"]
        else:
            current_project_dir = os.getenv("CURRENT_PROJECT_DIR")

        self.current_project = None
        if current_project_dir is not None:
            if current_project_dir in project_list:
                self.current_project = current_project_dir
        if self.current_project is None:
            self.current_project = project_list[0] if os.path.isdir(project_list[0]) else "D:/"
        self.comboBox_current_prod.setCurrentText(self.current_project)

        self.button_mode_asset.setChecked(True)
        self.mode = "assets"
        self.all_packages_dir = os.path.join(self.current_project,"assets")
        #self.package_Qlist.setCurrentRow(0)
        #self.package_Qlist_changed()

        #CONNECT WIDGET
        self.import_button.clicked.connect(self.import_clicked)
        self.open_folder.clicked.connect(self.open_folder_clicked)
        self.open_scene.clicked.connect(self.open_scene_clicked)
        self.copy_path.clicked.connect(self.copy_path_clicked)

        #Connect curent dir changed:
        self.comboBox_current_prod.currentTextChanged.connect(self.current_prod_changed)
        #Connect CHECKBOX
        self.sort_by_last_checkbox.clicked.connect(self.sort_by_last_clicked)
        self.button_return_previous.clicked.connect(self.button_return_previous_clicked)
        self.filter_text.textEdited.connect(self.filter_package_list)
        self.filter_departement.textEdited.connect(self.filter_departement_list)
        #Connect asset and shot buttons
        self.button_mode_asset.clicked.connect(self.button_mode_asset_clicked)
        self.button_mode_shot.clicked.connect(self.button_mode_shot_clicked)
        self.button_add_new.clicked.connect(self.button_add_new_clicked)

        self.reference_button.clicked.connect(self.reference_clicked)
        self.package_Qlist.itemSelectionChanged.connect(self.package_Qlist_changed)
        self.second_Qlist.itemSelectionChanged.connect(self.second_Qlist_changed)
        self.third_Qlist.itemClicked.connect(self.third_Qlist_changed)
        self.third_Qlist.itemDoubleClicked.connect(self.enter_directory)

        self.rebuild_package_list()


    ##############QLIST CHANGED ##############
    def package_Qlist_changed(self):
        """When in mode "Shot": rebuild the departement list (lighting, animation, etc.)
           When in mode "Asset": rebuild the shading list
        """

        packageName = self.package_Qlist.currentItem().text()
        if packageName:
            asset_browser_prefs["package_name"] = packageName
        self.package = Package(packageName, self.mode, self.current_project)
        if self.package.dir is not None:

            self.second_Qlist_refresh = False
            self.rebuild_departementList()
            self.second_Qlist_refresh = True

            if "departement_selection" in asset_browser_prefs:
                departement_selection = asset_browser_prefs["departement_selection"]
                for i in range(self.second_Qlist.count()):
                    item = self.second_Qlist.item(i)
                    if item.text() == departement_selection:
                        self.second_Qlist.setCurrentItem(item)
                        break

            self.rebuild_image()


    def second_Qlist_changed(self):
        current_item = self.second_Qlist.currentItem()
        if current_item is not None:
            text = current_item.text()
            departement_dir = os.path.join(self.package.dir,text)
            if self.second_Qlist_refresh:
                if departement_dir:
                    asset_browser_prefs["departement_selection"] = text
            self.rebuild_files_list(departement_dir)

    def third_Qlist_changed(self):
        path, namespace = self.build_path_scene()
        if path is not None:
            metadata = self.get_file_metadata(path)
            self.package_infos_label.setText(metadata)
        else:
            self.package_infos_label.setText("No files")

    #### REBUILD LIST ####

    def rebuild_package_list(self):
        self.clear_all_list()
        packages_list = os.listdir(self.all_packages_dir)
        self.clean_package_list = [package for package in packages_list if not_blacklisted(package)]

        for package in self.clean_package_list:
            item = QtWidgets.QListWidgetItem(package)
            self.package_Qlist.addItem(item)
            if "package_name" in asset_browser_prefs:
                if asset_browser_prefs["package_name"] == package:
                    self.package_Qlist.setCurrentItem(item)


    def filter_package_list(self):

        pattern = "*"+self.filter_text.text()+"*"
        filtered_package_list =  fnmatch.filter(self.clean_package_list, pattern)

        self.clear_all_list()
        for package in filtered_package_list:
            self.package_Qlist.addItem(package)

    ############## REBLUIDING LIST ##############
    def rebuild_departementList(self):
        """ List all the departements of the current selected shot"""
        self.second_Qlist.clear()
        self.second_Qlist.setSortingEnabled(False)

        self.departement_file_list, self.departement_dir_list = list_files_and_dirs_sorted(self.package.dir)
        self.filter_departement_list()

    def filter_departement_list(self):
        pattern = "*"+self.filter_departement.text()+"*"
        filtered_departement_dir_list =  fnmatch.filter(self.departement_dir_list, pattern)
        filtered_departement_file_list =   fnmatch.filter(self.departement_file_list, pattern)
        parent_dir = self.package.dir
        self.second_Qlist.clear()
        for dir_name in filtered_departement_dir_list:
            item = QtWidgets.QListWidgetItem()
            item.setText(dir_name)
            dir = os.path.join(parent_dir,dir_name)
            item.setData(QtCore.Qt.UserRole,dir)
            self.second_Qlist.addItem(item)

        item = QtWidgets.QListWidgetItem("----------------")
        item.setFlags(QtCore.Qt.ItemIsSelectable)
        self.second_Qlist.addItem(item)

        for file in filtered_departement_file_list:
            item = QtWidgets.QListWidgetItem()
            item.setText(file)
            dir = os.path.join(parent_dir,file)
            item.setData(QtCore.Qt.UserRole,dir)
            self.second_Qlist.addItem(item)
            item.setForeground(file_color_item)



        list_set_selected_byName(self.second_Qlist,self.package.favorite_dir)

    def rebuild_files_list(self,parent_dir):
        self.third_Qlist.clear()

        file_list, dir_list = list_files_and_dirs_sorted(parent_dir, self.sort_by_last_checkbox.isChecked())



        for dir_name in dir_list:
            item = QtWidgets.QListWidgetItem()
            item.setText(dir_name)
            dir = os.path.join(parent_dir,dir_name)
            item.setData(QtCore.Qt.UserRole,dir)
            self.third_Qlist.addItem(item)

        for file in file_list:
            item = QtWidgets.QListWidgetItem()
            item.setText(file)
            dir = os.path.join(parent_dir,file)
            item.setData(QtCore.Qt.UserRole,dir)
            self.third_Qlist.addItem(item)
            item.setForeground(file_color_item)
            self.third_Qlist.addItem(item)

        self.third_Qlist.setCurrentRow(0)
        self.third_Qlist_changed()


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


    ############## UTILITY FUNCTION  ##############

    def get_file_metadata(self, file_path):
        #size = os.path.getsize(file_path)
        #last_modified = os.path.getmtime(file_path)
        modificationTime = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')

        size = os.path.getsize(file_path)
        octet_size = convert_to_octet(size)

        metadatas = "Size: %s - Last modified: %s"%(octet_size  ,modificationTime  )
        return metadatas

    def clear_all_list(self):
        self.package_Qlist.clear()
        self.second_Qlist.clear()
        self.third_Qlist.clear()

    ### BUTTON CLICKED ###
    def sort_by_last_clicked(self):
        item = self.third_Qlist.currentItem()
        data = item.data(QtCore.Qt.UserRole)
        dir = os.path.dirname(data)
        self.rebuild_files_list(dir)


    def button_add_new_clicked(self):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog',
            'Name:')

        if ok:
            self.create_entity(str(text))

    def create_entity(self, name):

        mode = "assets" if self.button_mode_asset.isChecked() else "shots"
        path = os.path.join(self.current_project,mode,name)
        if os.path.isdir(path):

            cmds.confirmDialog( title='Warning',
                    message='Asset "%s" already exist. \n Creation impossible'%(name), )
            return
        template_directory = template_directories[mode]
        for task in template_directory:
            task_dir = os.path.join(path,task)
            os.makedirs(task_dir, exist_ok=True)

            #SKIPE DEFAULT SCENE CREATION IN NOT A MAYA TYPE
            if task not in maya_taks_template:
                continue

            task_file = os.path.join(task_dir,name+"_"+task+".0001.ma")
            if not os.path.isfile(task_file):
                absolute_path = os.path.dirname(os.path.realpath(__file__))
                scene_empty = os.path.join(absolute_path, "template","empty.ma")
                shutil.copy(scene_empty,task_file)

        self.rebuild_package_list()

    def button_mode_asset_clicked(self):
        if self.button_mode_asset.isChecked() and self.button_mode_shot.isChecked() ==True:
            self.mode = "assets"
            self.all_packages_dir = os.path.join(self.current_project,"assets")
            self.rebuild_package_list()
            self.button_mode_shot.setChecked(False)
        else:
            self.button_mode_asset.setChecked(True)
            pass

    def button_mode_shot_clicked(self):
        if self.button_mode_shot.isChecked() and self.button_mode_asset.isChecked() ==True:
            self.mode = "shots"
            self.all_packages_dir = os.path.join(self.current_project,"shots")
            self.rebuild_package_list()
            self.button_mode_asset.setChecked(False)
        else:
            self.button_mode_shot.setChecked(True)
            pass
    def current_prod_changed(self):
        self.current_project = self.comboBox_current_prod.currentText()
        asset_browser_prefs["current_project"] = self.current_project
        asset_browser_prefs.pop("package_name")
        asset_browser_prefs.pop("departement_selection")

        self.all_packages_dir = os.path.join(self.current_project,self.mode)
        self.rebuild_package_list()

    def build_path_scene(self):
        item_third = self.third_Qlist.currentItem()
        item_seconde = self.second_Qlist.currentItem()
        item = item_third if item_third is not None else item_seconde
        if item is None:
            return None, None

        data = item.data(QtCore.Qt.UserRole)
        namespace = os.path.splitext(item.text())[0]
        path = data
        return path, namespace

    def enter_directory(self,item):
        data = item.data(QtCore.Qt.UserRole)
        if os.path.isdir(data):
            self.rebuild_files_list(data)

    def button_return_previous_clicked(self):
        item = self.third_Qlist.currentItem()
        data = item.data(QtCore.Qt.UserRole)

        departement_dir =  self.second_Qlist.currentItem().data(QtCore.Qt.UserRole)
        if os.path.dirname(data) == os.path.join(self.package.dir,departement_dir):
            return
        dir = os.path.dirname(os.path.dirname(data))
        self.rebuild_files_list(dir)

    def import_clicked(self):
        path, namespace = self.build_path_scene()
        cmds.file(path, i=True, namespace=namespace)

    def reference_clicked(self):
        path, namespace = self.build_path_scene()

        if path.endswith(".ma") or path.endswith(".mb") or path.endswith(".abc"):
            cmds.file(path, reference=True,namespace=namespace)
        else:
            print("Not a maya scene")
    def open_folder_clicked(self):
        path, namespace = self.build_path_scene()
        if os.path.isdir(path):
            os.startfile(path)
        else:
            os.startfile(os.path.dirname(path))

    def copy_path_clicked(self):
        path, namespace = self.build_path_scene()
        forward_path = path.replace(os.sep, '/')
        copy2clip(forward_path)

    def open_scene_clicked(self):
        path, namespace = self.build_path_scene()
        if path.endswith(".ma") or path.endswith(".mb"):
            cmds.file(path, open=True, force=True)
        else:
            print("Not a maya scene !")

"""

try:

    ui.deleteLater()
except:
    pass
ui = AssetBrowser()
ui.create()
ui.show()
"""
