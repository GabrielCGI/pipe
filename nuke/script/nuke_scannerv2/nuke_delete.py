import nuke
import shutil
import os
import glob
from common.utils import *
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

# ######################################################################################################################

_PREFIX_TO_DELETE = "_TO_DELETE_"
SHOTS_DIR = 'Shots'
COMP_DIRS = os.path.join("Scenefiles", "Compo", "Compo")

# ######################################################################################################################

class ConfirmationNukeScanner(QDialog):
    def __init__(self,render_out_folder, data_renaming_folder, parent=None):
        super(ConfirmationNukeScanner, self).__init__(parent)

        # Model attributes
        self.__render_out_folder = render_out_folder
        self.__data_renaming_folder = data_renaming_folder

        # UI attributes
        self.__ui_width = 550
        self.__ui_height = 400
        self.__ui_min_width = 300
        self.__ui_min_height = 300
        center = QDesktopWidget().availableGeometry().center()
        offset = QPoint(int(self.__ui_width / 2), int(self.__ui_height / 2))
        self.__ui_pos = center - offset
        self.__tab_widget = None

        # name the window
        self.setWindowTitle("Confirmation Nuke Delete")
        # make the window a "tool" in Maya's eyes so that it stays on top when you click off
        self.setWindowFlags(QtCore.Qt.Tool)
        # Makes the object get deleted from memory, not just hidden, when it is closed.
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.__create_ui()
        self.__refresh_ui()


    def __create_ui(self):
        """
        Create the ui
        :return:
        """
        # Reinit attributes of the UI
        self.setMinimumSize(self.__ui_min_width, self.__ui_min_height)
        self.resize(self.__ui_width, self.__ui_height)
        self.move(self.__ui_pos)

        # Main Layout
        main_lyt = QVBoxLayout()
        self.setLayout(main_lyt)
        main_lyt.setContentsMargins(5, 8, 5, 8)

        title = QLabel("Are you sure you want to delete all these files?")
        main_lyt.addWidget(title, alignment=Qt.AlignCenter)

        self.__ui_list_folders = QListWidget()
        main_lyt.addWidget(self.__ui_list_folders)

        btn_lyt = QHBoxLayout()
        main_lyt.addLayout(btn_lyt)

        close_btn = QPushButton("Cancel")
        close_btn.clicked.connect(self.close)
        btn_lyt.addWidget(close_btn)
        accept_btn = QPushButton("Accept")
        accept_btn.clicked.connect(self.accept)
        btn_lyt.addWidget(accept_btn)

    def __refresh_ui(self):
        """
        Refresh the ui according to the model attribute
        :return:
        """
        self.__ui_list_folders.clear()
        for path in self.__data_renaming_folder:
            self.__ui_list_folders.addItem(QListWidgetItem(path))


def retrieve_shot():
        """
        Retrieve the current shot directory.
        If the directory structure matches expectations, set the shot directory.
        Otherwise, set it to None.
        """
        try:
            compo_filepath = nuke.root()['name'].value().replace("\\", "/")
        except AttributeError:
            shot_dir = None

        path_components = compo_filepath.split("/")
        
        # Localise if possible Scenefiles, Compo, Compo
        compo_dir_expected = None
        if len(path_components) > 8:
            compo_dir_expected = os.path.join(path_components[6], path_components[7], path_components[8])
        else:
            shot_dir = None

        if path_components[3] == SHOTS_DIR and \
           compo_dir_expected == COMP_DIRS:

            # Extract the desired path up to the "shot" directory.
            desired_path_components = path_components[:6]
            shot_dir = "/".join(desired_path_components)
        else:
            shot_dir = None

        return shot_dir

def get_every_folder_to_delete(render_out_folder):
    """ 
    Get every folder in the shot path that start with _PREFIX_TO_DELETE.
    
    :params render_out_folder: Location of layers of current comp
    :returns: A list of every folder to delete
    """
    
    shot_dir_pattern = os.path.join(render_out_folder, "*")
    folder_to_delete = []
    
    for layer_file_path in glob.glob(shot_dir_pattern):
        layer_basename = os.path.basename(layer_file_path)
        if layer_basename.startswith(_PREFIX_TO_DELETE):
            folder_to_delete.append(layer_file_path)
        else:
            version_pattern = os.path.join(shot_dir_pattern, "*")
            for version_file_path in glob.glob(version_pattern):
                version_basename = os.path.basename(version_file_path)
                if version_basename.startswith(_PREFIX_TO_DELETE):
                    folder_to_delete.append(version_file_path)
                    
    return folder_to_delete

def run():
    """
    Delete every folder that need to be deleted.
    """
    shot_dir = retrieve_shot()
    render_out_folder = os.path.join(
        os.path.normpath(shot_dir), "Renders", "3dRender")
    
    folder_to_delete = get_every_folder_to_delete(render_out_folder)
    
    render_out_folder_ui = shot_dir + "/Renders" + "/3dRender"
    
    if len(folder_to_delete)>0:
        if ConfirmationNukeScanner(
            render_out_folder_ui,
            folder_to_delete).exec_():
            
            for folder_path in folder_to_delete:
                print("DELETING %s"%(folder_path))
                try:
                    shutil.rmtree(folder_path)
                    print("\t Folder deleted : --> " + folder_path)
                except Exception as e:
                    print(f"Failed to delete:\n{e}")