# region Imports

# import other files
from . import texture_parser

# general imports
import sys
import glob
import os
from pathlib import Path
import subprocess
from enum import Enum

def import_qtpy():
    """
    Try to import qtpy from any prism install found in C:/ILLOGIC_APP/Prism.

    Returns:
        bool: True if the import path is found and False otherwise 
    """
    
    prism_qt_glob_pattern = "C:/ILLOGIC_APP/Prism/*/app/PythonLibs/*"

    found = False
    for path in glob.glob(prism_qt_glob_pattern):
        pyside_path = os.path.join(path, 'PySide')
        if os.path.exists(pyside_path):
            found = True
            break
    
    if not found:
        return False
    
    if pyside_path not in sys.path:
        sys.path.append(pyside_path)
    if path not in sys.path:
        sys.path.append(path)
    return True

# Import qt with qtpy of prism to match any version of qt found
# https://pypi.org/project/QtPy/
if not import_qtpy():
    sys.exit(1)
        
try:
    from qtpy import QtWidgets as Qt
    from qtpy import QtCore as Qtc
    from qtpy import QtGui as Qtg
except ImportError as e:
    sys.exit(1)

#imports for houdini 

try:
    import hou # type: ignore
except:
    pass

#endregion

class TreeHeaders(Enum):
    NAME = 0
    STATUS = 1
    PATH = 2 
    NODE = 3

#region Interface

OPEN = ["<b style=\"color: green;\">(" , "<b style=\"color: red;\">(" ]
CLOSE = ")</b>"
STATUS_TEXT = ["All files converted" , "Missing .rat files"]
TILE_ADDRESS_TOKENS = ["<UDIM>" , "$F"]

import socket
CONSTRUCTION = True
if socket.gethostname() == "SPRINTER-04" : 
    CONSTRUCTION = False

class MainInterface(Qt.QMainWindow):
    def __init__(self,
                 parent,
                 ):

        super(MainInterface, self).__init__(parent)

        self.setWindowTitle(".rat Manager")

        width = 1450
        height = 700
        self.resize(width, height)

        central = Qt.QWidget()
        self.setCentralWidget(central)
        self.layout = Qt.QHBoxLayout(central) 

        # Little splitter to seperate each section from one another
        self.splitter = Qt.QSplitter(central)
        self.splitter.setOrientation(Qtc.Qt.Horizontal)
        self.splitter.setObjectName("splitter")

        # Left side layout
        self.setup_texture_list()

        # Right side layout
        self.right_frame = Qt.QFrame(self.splitter)
        self.right_layout = Qt.QVBoxLayout(self.right_frame)

        self.setup_actions()
        self.setup_scene_options()

        # Init 
        self.rat_parser = texture_parser.TextureParser(ui = self)     
        self.layout.addWidget(self.right_frame)
        self.parse(True)

    def setup_texture_list(self) : 

        self.left_grp = Qt.QGroupBox('Texture list', self.splitter)
        self.left_layout = Qt.QVBoxLayout(self.left_grp)

        # Texture list
        self.texture_list: Qt.QTreeWidget = Qt.QTreeWidget()
        self.texture_list.setColumnCount(4)
        self.texture_list.setHeaderLabels(['Name', 'Status', 'Path', 'Node'])
        self.texture_list.setSelectionMode(Qt.QAbstractItemView.ExtendedSelection)
        self.texture_list.setContextMenuPolicy(Qtc.Qt.CustomContextMenu)
        
        self.texture_list.customContextMenuRequested.connect(self.openMenu)

        self.texture_list.setSortingEnabled(True)

        self.setStyleSheet("QTreeWidget::item { padding : 5px 0}")

        self.left_layout.addWidget(self.texture_list)
        self.layout.addWidget(self.left_grp)

        self.texture_list.itemSelectionChanged.connect(
            self.onSelectedLayerChanged
        )

    def setup_actions(self):

        self.actions_group = Qt.QGroupBox('Actions')
        sizePolicy = Qt.QSizePolicy(Qt.QSizePolicy.Preferred, Qt.QSizePolicy.Maximum)
        self.actions_group.setSizePolicy(sizePolicy)
        self.actions_layout = Qt.QVBoxLayout(self.actions_group)

        # TODO : Make sure the progress bar adapts its size to the other fella
        self.conversion_progress = None # init progress bar
        self.conversion_progress_val = 0

        self.convert_btn_layout = Qt.QHBoxLayout()

        # Convert selection button
        self.convert_selection_btn = Qt.QPushButton("Convert selected")
        self.convert_selection_btn.clicked.connect(self.convert_selection)
        self.convert_selection_btn.setEnabled(False)

        # Convert missing button
        self.convert_button = Qt.QPushButton("Convert all missing")
        self.convert_button.clicked.connect(self.convert)


        # Refresh button
        self.refresh_button = Qt.QPushButton("Refresh textures")

        self.refresh_button.clicked.connect(
            lambda: self.parse(True)
        )

        self.convert_btn_layout.addWidget(self.convert_selection_btn)
        self.convert_btn_layout.addWidget(self.convert_button)

        self.actions_layout.addLayout(self.convert_btn_layout)
        self.actions_layout.addWidget(self.refresh_button)

        self.right_layout.addWidget(self.actions_group)

    def setup_scene_options(self):

        self.scene_options_group = Qt.QGroupBox('Scene Options')
        sizePolicy = Qt.QSizePolicy(Qt.QSizePolicy.Preferred, Qt.QSizePolicy.Maximum)
        self.scene_options_group.setSizePolicy(sizePolicy)
        self.scene_options_layout = Qt.QFormLayout(
            self.scene_options_group)

        self.scene_include_layout = Qt.QVBoxLayout()
        self.scene_include_actions_layout = Qt.QHBoxLayout()

        self.scene_include = Qt.QListWidget()
        self.scene_include.setSelectionMode(Qt.QAbstractItemView.ExtendedSelection)

        self.scene_include_add = Qt.QPushButton('Add')
        self.scene_include_rm = Qt.QPushButton('Remove')
        self.scene_include_actions_layout.addWidget(self.scene_include_add)
        self.scene_include_actions_layout.addWidget(self.scene_include_rm)
        self.scene_include_layout.addWidget(self.scene_include)
        self.scene_include_layout.addLayout(self.scene_include_actions_layout)

        self.scene_options_layout.addRow(
            'Scan nodes', self.scene_include_layout)
        
        # self.scene_include.addItem("test_label")
        # self.scene_include.addItem("test_label") 
        # self.scene_include.addItem("test_label") 
        # self.scene_include.addItem("test_label") 
        
        # Scene include add 
        self.scene_include_add.clicked.connect(self.add_nodes)
    
        # Scene include remove
        self.scene_include_rm.clicked.connect(self.remove_nodes)
        self.right_layout.addWidget(self.scene_options_group)

    def parse(self , reset = True):

        """
        Using the functions from Texture parser, gets all our textures found and adds them to the table (name , path , has .rat)
        """

        self.rat_parser.find_textures_from_scene()
        self.rat_parser.find_convert_files()

        num_tex = len(self.rat_parser.get_all_texture_paths())
        self.update_scene_options()

        # Clear the list
        self.texture_list.clear()
        id = 0
        for item in self.rat_parser.texture_items : 
            texture_name = item.name

            # test = Qt.QTreeWidgetItem(None , ["Hiiii"])
            # self.texture_list.insertTopLevelItems(0 , [test])

            item_tex = item.get_num_tex()
            need_convert = item.get_num_toconv()
            
            if need_convert > 0: 
                text = "Missing " + str(need_convert) + "/" + str(item_tex)
                if need_convert == item_tex : 
                    status_label = Qt.QLabel(f"<b style=\"color: red;\"> {text} </b>")
                else : 
                    status_label = Qt.QLabel(f"<b style=\"color: orange;\"> {text} </b>")


            else : 
                text = 'All converted'
                status_label = Qt.QLabel(f"<b style=\"color: green;\"> {text} </b>")

            # TODO : make this a method in texture item interface
            nodes_str = item.nodes[0]
            for i in range(1, len(item.nodes)) : 
                nodes_str += ", " + item.nodes[i]

            texture_item = Qt.QTreeWidgetItem(None , [texture_name, '', item.texture_path, nodes_str])
            self.texture_list.insertTopLevelItems(id , [texture_item])
            self.texture_list.setItemWidget(texture_item , TreeHeaders.STATUS.value , status_label)


            tex_path = item.texture_path

            for i in range(len(item.get_children())) : 
                
                child = item.get_children()[i]

                name = child.name
                tex_path = child.texture_path

                # to_convert column: check if this path is in item.to_convert
                to_conv_list = self.rat_parser.files_to_convert
                if tex_path in to_conv_list : 
                    to_conv_text = "Missing .rat"
                    label = Qt.QLabel(f"<b style=\"color: red;\"> {to_conv_text} </b>")
                else : 
                    to_conv_text = "Has .rat"
                    label = Qt.QLabel(f"<b style=\"color: green;\"> {to_conv_text} </b>")                    

                test_child = Qt.QTreeWidgetItem(None , [name , '', tex_path])

                texture_item.addChild(test_child)
                # Add after the add child to actually apply the change
                self.texture_list.setItemWidget(test_child , 1 , label)


            id += 1
        

        # Deactivate the Convert button if no missing textures
        if not self.rat_parser.get_all_files_to_convert() : 
            self.convert_button.setEnabled(False)
        else : 
            self.convert_button.setEnabled(True)

        # Delete progress bar
        if reset and self.conversion_progress : 
            self.layout.removeWidget(self.conversion_progress)
            self.conversion_progress.deleteLater()
            self.conversion_progress = None


    def convert(self, id=None):

        """
        Using the functions from Texture parser, converts every texture without a .rat and updates the list
        """

        if id : 
            files_to_convert = self.rat_parser.texture_items[id].to_convert
        else : 
            files_to_convert = self.rat_parser.get_all_files_to_convert()

        if not files_to_convert : 
            return

        # Setup progress bar
        if not self.conversion_progress : 
            self.conversion_progress = Qt.QProgressBar(self)
            self.actions_layout.addWidget(self.conversion_progress)

            self.setStyleSheet("QProgressBar::chunk {background-color: green ; }")

        self.conversion_progress_val = 0
        self.conversion_progress.setValue(0)
        max_val = len(files_to_convert)
        self.conversion_progress.setMaximum(max_val)

        # disable the button while converting
        self.convert_button.setEnabled(False)

        # Call conversion function
        self.rat_parser.convert_to_rat(files_to_convert=files_to_convert)
    
    def convert_selection(self , id=None):

        files_to_convert = []
        for item in self.texture_list.selectedItems(): 
    
            item_name = item.data(TreeHeaders.NAME.value,0) 
            item_path = item.data(TreeHeaders.PATH.value,0)

            # Handle case where the whole UDIM is selected 
            # TODO : handle this with TextureFrames class maybe ?
            if "<UDIM>" in item_name or "$F" in item_name: 
                for i in range(item.childCount()) : 
                    child = item.child(i)
                    child_path = child.data(TreeHeaders.PATH.value,0)
                    if child_path : 
                        files_to_convert.append(child_path)
            elif item_path : 
                files_to_convert.append(item_path)


        # Setup progress bar
        if not self.conversion_progress : 
            self.conversion_progress = Qt.QProgressBar(self)
            self.actions_layout.addWidget(self.conversion_progress)

            self.setStyleSheet("QProgressBar::chunk {background-color: green ; }")

        self.conversion_progress_val = 0
        self.conversion_progress.setValue(0)
        max_val = len(files_to_convert)
        self.conversion_progress.setMaximum(max_val)

        self.rat_parser.convert_to_rat(files_to_convert=files_to_convert)

    def update_progress(self):
        self.conversion_progress_val += 1
        self.conversion_progress.setValue(self.conversion_progress_val)
        # Qt.QApplication.processEvents()

    def on_conversion_complete(self):
        """
        Called when all worker threads have finished
        """
        # Re-enable convert button
        self.convert_button.setEnabled(True)
        # Refresh the texture list
        self.parse(False)

    def open_in_explorer(self, current_item) :
        """
         (Merci Maxime)

         Input : Layer index 
         Output : Opens a directory of the file in that layer

        """

        parser_path = current_item.data(TreeHeaders.PATH.value, 0)
        if not parser_path : 
            parser_path = current_item.child(0).data(TreeHeaders.PATH.value, 0)

        directory_path = Path(parser_path).parent.as_uri()
        command = ['explorer.exe', directory_path]
        try:
            subprocess.run(command, capture_output=True)
        except Exception as e:
            print(f"Could not open {directory_path} in explorer \n{e}")
        
    def onSelectedLayerChanged(self):

        """
        (Merci Maxime)
        """

        selectedItem = self.texture_list.selectedItems()
        if selectedItem:
            self.convert_selection_btn.setEnabled(True)
        else :  
            self.convert_selection_btn.setEnabled(False)
    
    def openMenu(self, pos):
        self.menu = Qt.QMenu(self)
        current_item = self.texture_list.itemAt(pos)

        open_in_explorer_action = Qt.QAction("Open in explorer")
        open_in_explorer_action.triggered.connect(lambda : self.open_in_explorer(current_item))

        self.menu.addAction(open_in_explorer_action)
    
        self.menu.exec(self.texture_list.mapToGlobal(pos))

    def update_scene_options(self):
        self.scene_include.clear()
    
        for node_name in self.rat_parser.accepted_nodes:
            if not self.scene_include.findItems(node_name,Qtc.Qt.MatchExactly):
                self.scene_include.addItem(node_name)

    def add_nodes(self):

        text, ok =  Qt.QInputDialog.getText(self, "Add node",
                                            "Add nodes (seperated by space )", Qt.QLineEdit.Normal,
                                            "")
        if not (ok and text) :
            return 
        
        nodes = text.split(' ')
        for node in nodes :

            if self.scene_include.findItems(node,Qtc.Qt.MatchExactly):
                continue
        
            self.rat_parser.accepted_nodes.append(node)

        self.update_scene_options()
         

    def remove_nodes(self):
        for node_item in self.scene_include.selectedItems(): 
            node_name = node_item.text()
            self.rat_parser.accepted_nodes.remove(str(node_name))

        self.update_scene_options()

#endregion

#region Run

def run():
    '''
    Launches the Qt application
    '''

    instance = None
    if Qt.QApplication.instance():
        instance = hou.qt.mainWindow()
    
    my_window = MainInterface(
        parent = instance
    )
    my_window.show()

#endregion