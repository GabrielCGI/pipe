import os
import json
import importlib
import maya.OpenMayaUI as omui
import pymel.core as pm
from PySide2.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QAbstractItemView, 
                               QComboBox, QVBoxLayout, QWidget, QPushButton)
from PySide2.QtCore import Qt
from shiboken2 import wrapInstance

import abc_headless.export_abc_scenes as export_abc_scenes
importlib.reload(export_abc_scenes)

#project_list = ["I:/swaChristmas_2023", "I:/swaNY_2308", "I:/swaDisney_2307", "D:/", "I:/swaAlice_2309"]
project_list = [ "D:/"]

class ABCHWindow(QWidget):
    def __init__(self, parent=wrapInstance(int(omui.MQtUtil.mainWindow()), QWidget)):
        super(ABCHWindow, self).__init__(parent)

        self.setWindowTitle("Custom Window")
        self.setWindowFlags(Qt.Window)
        self.resize(850, 500)

        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        midl_layout = QVBoxLayout()
        righ_layout = QVBoxLayout()

        self.comboBox = QComboBox()
        self.comboBox.addItems(project_list)

        self.l_list = QListWidget()
        self.m_list = QListWidget()
        self.r_list = QListWidget()

        self.l_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.l_list.setMaximumWidth(200)
        self.m_list.setStyleSheet("background-color: #444444;")
        self.r_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.r_list.setMaximumWidth(200)

        self.export_button = QPushButton("Export Alembic", self)

        left_layout.addWidget(self.comboBox)
        left_layout.addWidget(self.l_list)
        midl_layout.addWidget(self.m_list)
        righ_layout.addWidget(self.r_list)
        righ_layout.addWidget(self.export_button)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(midl_layout)
        main_layout.addLayout(righ_layout)

        self.setLayout(main_layout)

        self.l_list.itemSelectionChanged.connect(self.updateSelectedFolders)
        self.comboBox.currentIndexChanged.connect(self.populateLeftList)
        self.comboBox.currentIndexChanged.connect(self.populateRightList)
        self.export_button.clicked.connect(self.retrieve_data)
        
        # Initialize
        self.populateLeftList()
        self.populateRightList()


    def populateLeftList(self):
        self.l_list.clear()

        selected_project = self.comboBox.currentText()
        shots_directory = os.path.join(selected_project, 'shots')

        folders = self.get_directories(shots_directory)
        self.l_list.addItems(folders)

    def get_directories(self, directory_path):
        if not os.path.exists(directory_path):
            return []

        return [folder for folder in os.listdir(directory_path)
                if os.path.isdir(os.path.join(directory_path, folder))]

    def populateRightList(self):
        self.r_list.clear()

        selected_project = self.comboBox.currentText()
        database_directory = os.path.join(selected_project, "assets/_database")

        txt_files = self.get_txt_files_from_directory(database_directory)
        for file in txt_files:
            geo_info = self.extract_name_from_file(file)
            for item in geo_info:
                self.r_list.addItem(item)

    def get_txt_files_from_directory(self, directory_path):
        txt_files = []

        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.txt'):
                    txt_files.append(os.path.join(root, file))

        return txt_files

    def extract_name_from_file(self, filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                return [data.get('name', "")]
        except json.JSONDecodeError:
            # Handle JSON decode error if needed
            return []

    def updateSelectedFolders(self):
        self.m_list.clear()

        selected_project = self.comboBox.currentText()
        selected_items = [item.text() for item in self.l_list.selectedItems()]
        selected_items.sort()

        for item_text in selected_items:
            custom_widget = QWidget()
            layout = QHBoxLayout()
            pad = 2
            layout.setContentsMargins(pad, pad, pad, pad)
            layout.addWidget(QLabel(item_text))

            combo = QComboBox()
            combo.setStyleSheet("background-color: #5d5d5d;")

            folder_path = os.path.join(selected_project, 'shots', item_text, 'anim')
            if os.path.exists(folder_path):
                # Get files with their full paths and filter by extension
                full_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                              if os.path.isfile(os.path.join(folder_path, f)) and f.endswith(('.ma', '.mb'))]
                # Sort files by modification date
                sorted_files = sorted(full_paths, key=os.path.getmtime, reverse=True)
                # Extract the base file names
                file_names = [os.path.basename(f) for f in sorted_files]
                
                if not file_names:
                    combo.addItem("No files found")
                else:
                    combo.addItems(file_names)
            else:
                combo.addItem("No files found")

            layout.addWidget(combo)
            custom_widget.setLayout(layout)

            item = QListWidgetItem(self.m_list)
            item.setSizeHint(custom_widget.sizeHint())
            item.setFlags(Qt.NoItemFlags)

            self.m_list.addItem(item)
            self.m_list.setItemWidget(item, custom_widget)

    def retrieve_data(self):
        
        characters = [item.text() for item in self.r_list.selectedItems()]
        selected_project = self.comboBox.currentText()
        database_directory = os.path.join(selected_project, "assets/_database")

        data_list = []
        for character in characters:
            for index in range(self.m_list.count()):
                widget = self.m_list.itemWidget(self.m_list.item(index))
                combo_box = widget.findChild(QComboBox)

                scene_path = None
                abc_path = None

                if combo_box.currentText() != "No files found":
                    scene_path = os.path.join(selected_project, 'shots', widget.findChild(QLabel).text(), 'anim', combo_box.currentText()).replace('\\', '/')
                    abc_path = os.path.dirname(scene_path).replace('/anim', '/abc')

                data = {
                    "character": character,
                    "scene_path": scene_path,
                    "abc_path": abc_path,
                    "database_path": database_directory
                }

                data_list.append(data)

        self.export_abc(data_list)

    def export_abc(self, data_list):

        for data in data_list:
            print("------")
            print(data["character"], data["scene_path"], data["abc_path"], "-0.125 0 0.125" , r"D:\log_file")
            print("------")

            # ????
            export_abc_scenes.export_all_headless(data["character"], data["scene_path"], data["abc_path"], "-0.125 0 0.125" , r"D:\log_file")