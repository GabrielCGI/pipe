# region Imports

# import other files
from . import texture_parser

# general imports
import sys
import glob
import os
from pathlib import Path
import subprocess

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

#region Interface

OPEN = ["<b style=\"color: green;\">(" , "<b style=\"color: red;\">(" ]
CLOSE = ")</b>"
STATUS_TEXT = ["All files converted" , "Missing .rat files"]


class TextureWidget(Qt.QWidget):
    
    """
    (Merci Maxime)

    Class to handle each individual element

    """
    
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.is_update = False

        self.mainLayout = Qt.QHBoxLayout()
        self.setLayout(self.mainLayout)
        
        self.label = Qt.QLabel(text)
        self.mainLayout.addWidget(self.label)
        self.mainLayout.addStretch()
        
        self.status_label = Qt.QLabel()
        self.mainLayout.addWidget(self.status_label)


    def sizeHint(self) -> Qtc.QSize:
        size = super().sizeHint()
        size += Qtc.QSize(0, 2)
        return size 


    def setUpdated(self, on: bool, extra_text = ""):
        self.is_update = on
        if self.is_update:
            self.status_label.setText(OPEN[0] + STATUS_TEXT[0] + extra_text + CLOSE) # Does not need conversion
        else:
            self.status_label.setText(OPEN[1] + STATUS_TEXT[1] + extra_text + CLOSE) # Needs conversion



class TextureList(Qt.QListWidget):
    
    """
    (Merci Maxime)

    Class to handle the list of our textures
    """
    
    def __init__(self, ui, parent=None):
        super().__init__(parent)
        self.main_ui = ui
        
        
    def buildMenu(self, menu: Qt.QMenu) -> Qt.QMenu:
        selected_indexes = self.selectedIndexes()
        if not selected_indexes:
            return
        current_index = selected_indexes[0].row()
        
        openexplorerAction = menu.addAction("Open in Explorer")
        openexplorerAction.triggered.connect(
            lambda: self.main_ui.open_in_explorer(current_index)
        )

        # FIXME : Not entirely working yet, saves to the wrong directory
        # convertSpecificTexAction = menu.addAction("Convert only this texture")
        # convertSpecificTexAction.triggered.connect(
        #     lambda : self.main_ui.convert(current_index)
        # )
        
        return menu

    def contextMenuEvent(self, event: Qtg.QContextMenuEvent):
        contextmenu = Qt.QMenu(self)
        contextmenu = self.buildMenu(contextmenu)
        if hasattr(contextmenu, 'exec'):
            contextmenu.exec(event.globalPos())
        elif hasattr(contextmenu, 'exec_'):
            contextmenu.exec_(event.globalPos())

class MainInterface(Qt.QMainWindow):
    def __init__(self,
                 parent,
                 ):
        
        """
        
        Create the main window

        """

        super(MainInterface, self).__init__(parent)

        self.setWindowTitle(".rat file converter")

        width = 800
        height = 900
        self.resize(width, height)

        central = Qt.QWidget()
        self.setCentralWidget(central)
        self.layout = Qt.QVBoxLayout(central) 
            
        # Refresh button
        parse_button = Qt.QPushButton("Refresh textures")
        parse_button.clicked.connect(self.parse)
        self.layout.addWidget(parse_button)
        

        #############################################################

        # Taken from Maxime's thing, should pretty easily make it work
        # Replace my tables with the layer list but figure out how dat work first

        texture_layout = Qt.QHBoxLayout()
        self.layout.addLayout(texture_layout)
        
        self.texture_list = TextureList(self)
        texture_layout.addWidget(self.texture_list, 33)
        
        self.QTabTextures = Qt.QTabWidget()
        # set stylesheet to prevent prism pipeline overriding it
        self.QTabTextures.setStyleSheet("QTabWidget::tab-bar {alignment: left;}")
        self.QTabTextures.tabBar().hide()
        
        self.texture_list.itemSelectionChanged.connect(
            self.onSelectedLayerChanged
        )
        
        texture_layout.addWidget(self.QTabTextures, 67)

        #############################################################

        # Number of textures found
        self.num_tex_label = Qt.QLabel()
        # Fill the table and the number of textures
        self.parse()
        self.layout.addWidget(self.num_tex_label)
    
        # Convert to .rat button
        self.convert_button = Qt.QPushButton("Convert to .rat")
        self.convert_button.clicked.connect(self.convert)
        self.layout.addWidget(self.convert_button)

        # progress bar init
        self.conversion_progress = None
        self.conversion_progress_val = 0


        
    def parse(self):

        """
        Using the functions from Texture parser, gets all our textures found and adds them to the table (name , path , has .rat)
        """

        self.rat_parser = texture_parser.TextureParser(ui = self)     
        
        num_tex = len(self.rat_parser.get_all_texture_paths())

        self.num_tex_label.setText(f"Number of textures found : {num_tex}")

        # Clear the list
        self.texture_list.clear()

        self.QTabTextures.clear()

        for item in self.rat_parser.textures : 
            layer_text = item.name
            layer_widget = TextureWidget(layer_text)
            layer_item = Qt.QListWidgetItem()

            item_tex = item.get_num_tex()
            need_convert = item.get_num_toconv()

            if need_convert > 0: 
                text = " " + str(need_convert) + "/" + str(item_tex)
                layer_widget.setUpdated(False, text)
            else : 
                layer_widget.setUpdated(True)  

            self.texture_list.addItem(layer_item)
            self.texture_list.setItemWidget(layer_item, layer_widget)
            layer_item.setSizeHint(layer_widget.sizeHint())



            table = Qt.QTableWidget()
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(["Name" , "Path" , "Has .rat"])

            tex_paths = item.texture_paths

            table.setRowCount(len(tex_paths))

            for row, tex_path in enumerate(tex_paths) : 

                name = self.rat_parser.get_texture_name(tex_path)

                name_item = Qt.QTableWidgetItem(name) # name
                table.setItem(row, 0, name_item)

                path_item = Qt.QTableWidgetItem(tex_path)
                table.setItem(row, 1, path_item)

                # to_convert column: check if this path is in item.to_convert
                to_conv_list = item.to_convert
                to_conv_text = "" if tex_path in to_conv_list else "X"
                conv_item = Qt.QTableWidgetItem(to_conv_text)
                conv_item.setTextAlignment(Qtc.Qt.AlignmentFlag.AlignCenter)

                table.setItem(row, 2, conv_item)


            #table.setEditTriggers(Qt.QAbstractItemView.NoEditTriggers)
            table.setSelectionBehavior(Qt.QAbstractItemView.SelectRows)
            table.horizontalHeader().setSectionResizeMode(Qt.QHeaderView.Stretch)
            table.verticalHeader().setVisible(False)

            self.QTabTextures.addTab(table, item.name)


    def convert(self, id=None):

        """
        Using the functions from Texture parser, converts every texture without a .rat and updates the list
        """

        if id : 
            files_to_convert = self.rat_parser.textures[id].to_convert
        else : 
            files_to_convert = self.rat_parser.get_all_files_to_convert()

        # Setup progress bar
        self.conversion_progress_val = 0
        self.conversion_progress.setValue(0)
        max_val = len(files_to_convert)
        self.conversion_progress.setMaximum(max_val)

        if not self.conversion_progress : 
            self.conversion_progress = Qt.QProgressBar(self)
            self.layout.addWidget(self.conversion_progress)

        # Call conversion function
        self.rat_parser.convert_to_rat(files_to_convert=files_to_convert)

        # refresh the texture list
        self.parse()

    def open_in_explorer(self , current_index) :
        """
         (Merci Maxime)

         Input : Layer index 
         Output : Opens a directory of the file in that layer

        """

        parser_path = self.rat_parser.textures[current_index].texture_paths[0]

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
            current_index = self.texture_list.indexFromItem(selectedItem[0])
            self.QTabTextures.setCurrentIndex(
                current_index.row()
            )
    

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