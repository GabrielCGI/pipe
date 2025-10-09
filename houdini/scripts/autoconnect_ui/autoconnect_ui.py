import os
import re
import sys
import glob
import hou
from pathlib import Path

from . import houdinilog as hlog
from . import auto
from . import shader as sh
from . import map as mp

try:
    from PySide2 import QtCore
    from PySide2 import QtWidgets
    QT_FOUND = True
except:
    try:
        from PySide6 import QtCore
        from PySide6 import QtWidgets
        QT_FOUND = True
    except:
        QT_FOUND = False
    
from enum import Enum

QSS_STYLESHEET_PATH = os.path.join(
                                   os.path.dirname(__file__),
                                   "ressource",
                                   "autoconnect_stylesheet.qss")
DEFAULT_VALUE_CBBOX = "----"    

class MapState(Enum):
    CAN_BE_UPDATED = 'can_be_updated'
    NEW = 'new'
    ALREADY_UPDATED = 'already_uptead'
    
    def description(self):
        return {
            MapState.CAN_BE_UPDATED: "<font color='orange'>"
                                     + "(Can Be Updated) </font>",
            MapState.NEW: "<font color='red'>(New) </font>",
            MapState.ALREADY_UPDATED: "<font color='green'>"
                                     + "(Already Updated) </font>",
        }[self]
    
class MapWidget(QtWidgets.QWidget):
    
    def __init__(
            self, mapName: str,
            old_version: str=None, version: str=None,
            listVersion: list[str]=None, versioning=False,
            parent=None):
        """
        Initialize a MapWidget with versioning or not.
        
        Args:
            mapName (str): Map name.
            version (str, optional): Latest version found.
            listVersion (list[str], optional): All versions of this map.
            versioning (bool, optional): If versioning enable.
            parent (QtWidgets.QWidget, optional): Parent widget. 
        """
        
        QtWidgets.QWidget.__init__(self, parent)

        self.mapName = mapName
        self.old_version = old_version
        self.version = version
        self.listVersion = listVersion
        self.versioning = versioning
        
        self.state = MapState.NEW
        self.latestVersion = None

        self.initializeMapWidget()
    
    
    def initializeMapWidget(self):
        """
        Setup map widget layouts and widgets. 
        """
          
        hbox = QtWidgets.QHBoxLayout()
        
        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setChecked(True)
        hbox.addWidget(self.checkbox)
        
        self.mapNameLabel = QtWidgets.QLabel()
        self.mapNameLabel.setText(self.mapName)
        hbox.addWidget(self.mapNameLabel)
        
        self.spacer = QtWidgets.QWidget()
        self.spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred)
        
        if self.versioning:
            self.listVersion.sort()
            self.latestVersion = self.listVersion[-1]
            
            self.versions: list[str] = self.listVersion
            self.versionsLabel = QtWidgets.QLabel()
            self.setVersionText(self.old_version, self.version)
            if self.state == MapState.ALREADY_UPDATED:
                self.checkbox.setChecked(False)
            
            hbox.addWidget(self.spacer)
            hbox.addWidget(self.versionsLabel)
        
            self.versionComboBox = QtWidgets.QComboBox()
            self.versionComboBox.addItems(self.listVersion)
            self.versionComboBox.setCurrentText(self.version)
            self.versionComboBox.currentTextChanged.connect(
                self.onVersionChanged)
            hbox.addWidget(self.versionComboBox)
        else:
            
            self.stateLabel = QtWidgets.QLabel()
            self.stateLabel.setText(self.state.description())
            hbox.addWidget(self.stateLabel)
            
            hbox.addWidget(self.spacer)
                
        self.setLayout(hbox)

    def setVersionText(self, old_version, version):
        """
        Update text depending of map state and selected version.
        
        Args:
            old_version (str): Selected map version.
            version (str): Last version available.
        """
        
        if old_version is not None:
            if (old_version == self.latestVersion):
                self.state = MapState.ALREADY_UPDATED
                self.versionsLabel.setText(
                    f"{self.state.description()}"
                    + f"{version}")
            else:
                self.state = MapState.CAN_BE_UPDATED
                self.versionsLabel.setText(
                    f"{self.state.description()}"
                    + f"{old_version} --> {version}")
        else:
            self.state = MapState.NEW
            self.versionsLabel.setText(
                f"{self.state.description()}"
                + f"{version}")
        
        parent = self.parent()
        if parent is not None:
            shaderWidget: ShaderWidget = parent.parent()
            if shaderWidget is not None:
                shaderWidget.updateState()
        

    def onVersionChanged(self):
        """
        Slot when version change to update text.
        """
        
        currentVersion = self.versionComboBox.currentText()
        self.setVersionText(self.old_version, currentVersion)
        
    def getVersions(self):
        """
        Get current version if versioning is enable.
        """
        
        if self.versioning:
            return self.versions
        
class ShaderWidget(QtWidgets.QTreeWidget):
    """
    Custom QTreeWidget used to display all maps of a shader.
    """
    
    def __init__(self, shaderName, maps, versioning=False, color=None, parent=None):
        """
        Initialize a shaderwidget with a versioning, or not.
        
        Args:
            shaderName (str): Shader name.
            maps (list[MapWidget]): A list of initialized map widget.
            versioning (bool, optional): Flag telling if versioning is enable.
            parent (QtWidgets.QWidget, optional): Parent widget. 
        """    
        
        QtWidgets.QTreeWidget.__init__(self, parent)
        
        self.shaderName = shaderName
        self.maps = maps
        self.versioning = versioning
        self.color = color
        
        self.mapWidgets: MapWidget = []
        self.currentState = MapState.NEW
        
        self.initializeShaderWidget()
        
    def initializeShaderWidget(self):
        self.mainItemWidget = QtWidgets.QWidget()
        hbox = QtWidgets.QHBoxLayout()
        
        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(self.onSelectChanged)
        hbox.addWidget(self.checkbox)
        
        self.mapNameLabel = QtWidgets.QLabel()    
        self.mapNameLabel.setText(self.shaderName)
        self.mapNameLabel.setObjectName("shaderName")
        hbox.addWidget(self.mapNameLabel)
        
        self.stateLabel = QtWidgets.QLabel()
        hbox.addWidget(self.stateLabel)
        
        self.spacer = QtWidgets.QWidget()
        self.spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred)
        hbox.addWidget(self.spacer)
        
        self.colorWidget = QtWidgets.QWidget()
        self.spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred)
        self.colorWidget.setMinimumWidth(300)
        self.colorWidget.setObjectName("colorWidget")
        hbox.addWidget(self.colorWidget)
        
        if self.versioning:
            self.versionComboBox = QtWidgets.QComboBox()
            self.versionComboBox.currentTextChanged.connect(
                self.onVersionChanged)
            hbox.addWidget(self.versionComboBox)
        
        self.mainItemWidget.setObjectName("mainItemWidget")
        self.mainItemWidget.setLayout(hbox)
        
        self.updateStyle()
        
        # Settings et slot du treewidget
        self.initializeTreeSettings()
        
        self.mainItem = QtWidgets.QTreeWidgetItem()
        self.addTopLevelItem(self.mainItem)
        self.setItemWidget(self.mainItem, 0, self.mainItemWidget)
        
        self.mainItem.setExpanded(True)
        
        self.setMapWidgets(self.maps)
    
    def setColor(self, color):
        self.color = color
        self.updateStyle()
        
    def updateStyle(self):
        """
        Set qss style relative to the shader color
        """
        
        if self.color is not None:
            rgb_css = f"rgb({self.color[0]*255},"\
                      + f" {self.color[1]*255}, {self.color[2]*255})"
            background_color = f"background: {rgb_css};"
            self.setStyleSheet(f"QWidget#colorWidget {{{background_color}}}"\
                               + f"QLabel#shaderName {{color: {rgb_css};}}")
    
    def initializeTreeSettings(self):
        """
        Initialize Shader tree attributes and slots.
        """
        
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setColumnCount(1)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)
        self.itemPressed.connect(self.onItemPressed)
        self.collapsed.connect(self.adjustSize)
        self.expanded.connect(self.adjustSize)
        
    
    def getVersions(self):
        """
        Get the intersection of every versions availables.
        """
        
        versions = [DEFAULT_VALUE_CBBOX]
        for mapWidget in self.mapWidgets:
            versions += mapWidget.getVersions()
        versions = list(set(versions))
        versions.sort()
        return versions
        
    def updateState(self):
        """
        Update current shader state and text based on maps states.
        """
        
        everyStateNew = True
        everyStateAlreadyUpdated = True
        anyStateCanBeUpdated = False
        
        for mapWidget in self.mapWidgets:
            if mapWidget.state != MapState.NEW:
                everyStateNew = False
            if mapWidget.state != MapState.ALREADY_UPDATED:
                everyStateAlreadyUpdated = False
            if not anyStateCanBeUpdated:
                if mapWidget.state == MapState.CAN_BE_UPDATED:
                    anyStateCanBeUpdated = True
                    break
                
        if (not everyStateNew and not everyStateAlreadyUpdated):
            self.currentState = MapState.CAN_BE_UPDATED
            self.stateLabel.setText(
                f"{self.currentState.description()}")
        elif everyStateNew:
            self.currentState = MapState.NEW
            self.stateLabel.setText(
                f"{self.currentState.description()}")
        elif everyStateAlreadyUpdated:
            self.currentState = MapState.ALREADY_UPDATED
            self.stateLabel.setText(
                f"{self.currentState.description()}")
        else:
            # Default state of new (but cannot happens)
            self.currentState = MapState.NEW
            self.stateLabel.setText(
                f"{self.currentState.description()}")
    
    
    def setMapWidgets(self, mapWidgets):
        """
        Set maps widgets as a children of the shader treewidget.
        
        Args:
            mapWidgets (list[mapWidgets]): List of initialized map widgets.
        """
        
        self.mapWidgets = mapWidgets
        
        for mapWidget in self.mapWidgets:
            item = QtWidgets.QTreeWidgetItem()
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsSelectable)
            self.mainItem.addChild(item)
            self.setItemWidget(item, 0, mapWidget)
        
        self.updateState()
        
        if self.currentState == MapState.ALREADY_UPDATED:
            self.collapseAll()
            self.checkbox.setChecked(False)
            self.onSelectChanged()
        
        if self.versioning:  
            self.versionComboBox.clear()
            self.versionComboBox.addItems(self.getVersions())

    def adjustSize(self):
        """
        Adjust tree widget size when collapsed or expanded.
        """
        
        rowHeight = self.rowHeight(self.model().index(0, 0, self.rootIndex()))
        
        # Offset to avoid scrollbar
        rowHeight += 1
        if not self.isItemExpanded(self.mainItem):
            self.setFixedHeight(rowHeight)
        else:
            self.setFixedHeight(rowHeight * (len(self.mapWidgets)+1))

    def onSelectChanged(self):
        
        if not self.checkbox.isChecked():
            for i in range(self.mainItem.childCount()):
                item = self.mainItem.child(i)
                self.itemWidget(item, 0).setEnabled(False)
        else:
            self.expandAll()
            for i in range(self.mainItem.childCount()):
                item = self.mainItem.child(i)
                self.itemWidget(item, 0).setEnabled(True)
            
    def onVersionChanged(self):
        """
        Slot to update maps widgets version from shader version.
        """
        
        currentVersion = self.versionComboBox.currentText()
        if (currentVersion != DEFAULT_VALUE_CBBOX):
            for mapWidget in self.mapWidgets:
                mapWidget.versionComboBox.setCurrentText(currentVersion)
            
    def onItemPressed(self, item, column):
        """
        Slot when an item is pressed to expand and collapse tree
        and to check and uncheck item.
        """
        
        if item == self.mainItem:
            if item.isExpanded():
                self.collapseAll()
            else:
                self.expandAll()
            self.clearSelection()
            return
        
        itemWidget = self.itemWidget(item, 0)
        if itemWidget.isEnabled() and itemWidget.checkbox:
            itemWidget.checkbox.setChecked(
                not itemWidget.checkbox.isChecked())
    
    def showEvent(self, event):
        super().showEvent(event)
        self.adjustSize()
        
               
class AutoConnectUI(QtWidgets.QMainWindow):
    
    def __init__(self, material_library, parent=None):
        """
        Initialize a pyside MainWindow.
        
        Args:
            dir_path (str): Directory to parse maps.
            material_library (hou.Node): Houdini node to store shaders.
            parent (QtWidgets.QWidget, optional): Parent widget. 
        """
        
        QtWidgets.QMainWindow.__init__(self, parent)
        
        self.setGeometry(500, 300, 800, 600)
        self.setMinimumSize(800, 600)
        self.setWindowTitle('Autoconnect')
        
        self.initializeStyleSheet()
        
        self.material_library = None
        self.dir_path = None
        self.selectedShaders = None
        self.shaders = []
        self.subnets = []
        self.shaderWidgets: ShaderWidget = []
        
        self.initializeCentralWidget()
        self.onRefresh()
        self.initializeToolbar()
        
        self.initialized = not self.material_library is None
        
    def initializeStyleSheet(self):
        """
        Initialize UI qss.
        """
        
        try:
            with open(QSS_STYLESHEET_PATH, "r") as f:
                stylesheet = f.read()
                self.setStyleSheet(stylesheet)
        except Exception as e:
            hlog.pdebug(f"Could not load stylesheet:\n\t{e}")


    def initializeCentralWidget(self):
        """
        Initialize a central scrolling widget to hold shader widgets.
        """
        
        self.scrollarea = QtWidgets.QScrollArea()
        
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setObjectName("scrollarea")
        self.scrollarea.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn)

        self.central = QtWidgets.QWidget()
        self.central.setMinimumWidth(600)
        self.central.setObjectName("centralWidget")
        
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setAlignment(QtCore.Qt.AlignTop)

        self.initializeShaderWidgets()
        self.setupShaderWidgets()

        self.central.setLayout(self.vbox)
        self.scrollarea.setWidget(self.central)
        self.setCentralWidget(self.scrollarea)


    def initializeToolbar(self):
        """
        Initialized a tooblar with basic buttons.
        """
        
        self.toolbar = QtWidgets.QToolBar()
        
        self.openFileButton = QtWidgets.QPushButton()
        self.openFileButton.setText("Open file...")
        self.openFileButton.clicked.connect(self.onOpenDirectory)
        self.toolbar.addWidget(self.openFileButton)
        
        self.clearButton = QtWidgets.QPushButton()
        self.clearButton.setText("Clear")
        self.clearButton.clicked.connect(self.clearVBOX)
        self.toolbar.addWidget(self.clearButton)
        
        self.refreshButton = QtWidgets.QPushButton()
        self.refreshButton.setText("Refresh")
        self.refreshButton.clicked.connect(self.onRefresh)
        self.toolbar.addWidget(self.refreshButton)
        
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)
        
        self.applyButton = QtWidgets.QPushButton()
        self.applyButton.setText("Apply")
        self.applyButton.clicked.connect(self.onCreate)
        self.toolbar.addWidget(self.applyButton)
        
        self.toolbar.setMovable(False)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.toolbar)
    
    
    def initializeShaderWidgets(self):
        """
        Initialized shader widget from existing sh.Shader object.
        """
        
        for shader in self.shaders:
            listMapWidgets = []
            if isinstance(shader, sh.VersionShader):
                shader.setLatestMap()
                existingSubnet = auto.get_existing_subnet(
                    self.material_library, shader.name)
                
                existingShader: sh.VersionShader = None
                subnet_color = None
                if existingSubnet is not None:
                    existingShader = auto.get_shader_from_subnet(
                        existingSubnet)
                    subnet_color = existingSubnet.color().rgb()
                    
                for map in shader.maps:
                    listVersion = []
                    
                    for mapVersion in shader.allVersionsMaps[map.name]:
                        listVersion.append(mapVersion.version)
                    
                    old_version = None
                    if existingShader is not None:
                        existingMap = existingShader.existMaps(map)
                        if existingMap is not None:
                            old_version = existingShader.allVersionsMaps[existingMap][0].version
                            
                    mapWidget = MapWidget(
                        mapName=map.name, old_version=old_version,
                        version=map.version, listVersion=listVersion,
                        versioning=True)
                    listMapWidgets.append(mapWidget)
                shaderWidget = ShaderWidget(
                    shader.name, listMapWidgets,
                    versioning=True, color=subnet_color)
                self.shaderWidgets.append(shaderWidget)
            else:
                for map in shader.maps:
                    mapWidget = MapWidget(mapName=map.name, versioning=False)
                    listMapWidgets.append(mapWidget)
                shaderWidget = ShaderWidget(
                    shader.name, listMapWidgets, versioning=False)
                self.shaderWidgets.append(shaderWidget)      
            
            
    def setupShaderWidgets(self):
        """
        Add shader widget to vbox layout.
        """
        
        new_shader = []
        for shaderWidget in self.shaderWidgets:
            if shaderWidget.color is None:
                new_shader.append(shaderWidget)
        
        for i, shaderWidget in enumerate(self.shaderWidgets):
            
            hbox = QtWidgets.QHBoxLayout()
            
            labelShader = QtWidgets.QLabel(
                f"<h4>Shader {i+1}:</h4>")
            hbox.addWidget(labelShader)
            
            labelName = QtWidgets.QLabel(
                f"<h4>{shaderWidget.shaderName}</h4>"
            )
            
            color = None
            if shaderWidget in new_shader:
                r, g, b = auto.getColor(
                    i, len(self.shaderWidgets))
                color = hou.Color(r, g, b).rgb()
                shaderWidget.setColor(color)
            else:
                color = shaderWidget.color
            if color is not None:
                labelName.setStyleSheet(
                    f"color: rgb({color[0]*255}, "
                    f"{color[1]*255}, "
                    f"{color[2]*255})")
            
            hbox.addWidget(labelName)
            
            widget = QtWidgets.QWidget()
            widget.setLayout(hbox)
            self.vbox.addWidget(widget)        
            widget.setSizePolicy(
                QtWidgets.QSizePolicy.Fixed,
                QtWidgets.QSizePolicy.Fixed)
            
            self.vbox.addWidget(shaderWidget)
    
    
    def readShaders(self):
        """
        Read shader widgets as sh.Shader to be able to build them.
        """
        
        self.shadersToUpdate = []
        for shaderWidget in self.shaderWidgets:
            if shaderWidget.checkbox.isChecked():
                
                shaderFound = False
                for shader in self.shaders:
                    if shader.name == shaderWidget.mapNameLabel.text():
                        shaderFound = True
                        self.shadersToUpdate.append(shader)
                        break
                
                if not shaderFound:
                    continue
                
                anyMapChecked = False
                
                shader: sh.Shader = self.shadersToUpdate[-1]
                shader.selected_maps.clear()
                if isinstance(shader, sh.VersionShader):
                    
                    toggleSpecificVersion = False
                    if (shaderWidget.versionComboBox.currentText()
                        != DEFAULT_VALUE_CBBOX):
                        toggleSpecificVersion = True
                
                    for mapWidget in shaderWidget.mapWidgets:
                        if mapWidget.checkbox.isChecked():
                            anyMapChecked = True
                            
                            version = None
                            if toggleSpecificVersion:
                                version = shaderWidget\
                                    .versionComboBox.currentText()
                            else:
                                version = mapWidget\
                                    .versionComboBox.currentText()
                            listVersion = shader\
                                .allVersionsMaps[
                                    mapWidget.mapNameLabel.text()
                                ]
                            for map in listVersion:
                                if map.version == version:
                                    shader.selected_maps.append(map)
                                    break
                else:
                    for mapWidget in shaderWidget.mapWidgets:
                        if mapWidget.checkbox.isChecked():
                            anyMapChecked = True
                            for map in shader.maps:
                                if map.name == mapWidget.mapNameLabel.text():
                                    shader.selected_maps.append(map)
                                    break
                
                if not anyMapChecked:
                    self.shadersToUpdate.pop()
    
    
    def checkSelectedNodes(self) -> list:
        """Get a list of material builder from a material library node or
        a selection of material builder and set the materiallibrary attribute.
        
        Returns:
            list: list of material builder
        """        
        
        # Check if the material library node is selected
        selectedNodes = hou.selectedNodes()
        
        if not len(selectedNodes):
            hlog.pinfo("Please selected a material library or some shaders.")
            hou.ui.displayMessage("Please selected a material "
                                  "library or some shaders")
            return []
        
        material_library_selected = False
        shaders_selected = False
        
        if selectedNodes[0].type().name() == 'materiallibrary':
            material_library_selected = True
        elif selectedNodes[0].parent().type().name() == 'materiallibrary':
            shaders_selected = True
        else:
            hlog.pinfo("Please selected a material library or some shaders.")
            hou.ui.displayMessage("Please selected a material "
                                  "library or some shaders")
            return []
        
        subnets = []
        if material_library_selected:
            self.material_library = selectedNodes[0]
            subnets += self.material_library.children()
            
            self.selectedShaders = []
            for subnet in self.material_library.children():
                self.selectedShaders.append(subnet.name())
            
        elif shaders_selected:
            self.material_library = selectedNodes[0].parent()
            subnets += selectedNodes
            
            self.selectedShaders = []
            for node in selectedNodes:
                self.selectedShaders.append(node.name())
                
        else:
            hlog.pinfo("Unexpected state: neither material"
                       " library nor shaders are selected.")
            hou.ui.displayMessage("An unexpected error occurred.")
            return []
        
        return subnets
    
    
    def changeActivePane(self):
        """
        Active network panel and focus material library.
        """
        
        netpane = None
        for pane in hou.ui.paneTabs():
            if pane.type() == hou.paneTabType.NetworkEditor:
                netpane = pane
                break

        if netpane is None:
            hlog.pdebug("Network panel is not active.")
            hou.ui.displayMessage("Network panel is not active.")
            return []
        else:
            netpane.setPwd(self.material_library)
    
    
    def findDirectory(self, subnets):
        """
        Find every files candidates for an update based on shader already
        present in a material library.
        
        Warning: Multiple usages of recursive glob search, potentially
        computationnal heavy.
        """

        map_list_per_subnet = []
        for subnet in subnets:
            map_list_per_subnet.append([])
            has_map = False
            for node in subnet.children():
                if node.type().name() == 'mtlximage':
                    has_map = True
                    map_path = node.parm('file').eval()
                    if map_path is not None:
                        map_list_per_subnet[-1].append(map_path)
            if not has_map:
                self.selectedShaders.remove(subnet.name())
                map_list_per_subnet.pop()
          
        file_list = []
        for i, subnet_map_list in enumerate(map_list_per_subnet):
            file_list.append([])
            for map_name in subnet_map_list:
                versionMatch = re.search(mp.VERSION_PATTERN, map_name)
                if versionMatch is None:
                    file_list[i].append(map_name)
                else:
                    versionSpan = versionMatch.span()
                    globpath = map_name[:versionSpan[0]]\
                               + "*" + map_name[versionSpan[1]:]
                    
                    udimMatch = re.search(".<UDIM>", globpath)
                    if udimMatch:
                        udimSpan = udimMatch.span()
                        globpath = globpath[:udimSpan[0]]\
                                   + "*" + globpath[udimSpan[1]:]
                        
                    file_list[i] += glob.glob(pathname=globpath)
            file_list[i] = list(set(file_list[i]))
        
        return file_list
        
                        
    def onCreate(self):
        """
        Slot to create selected shaders.
        """
        
        self.readShaders()
        
        if not auto.ask_confirmation(self.shadersToUpdate):
            return
        
        self.changeActivePane()
        
        for shader in self.shadersToUpdate:
            color = None
            for shaderWidget in self.shaderWidgets:
                if shader.name == shaderWidget.mapNameLabel.text():
                    color = hou.Color(shaderWidget.color)
            auto.create_shader_network(
                shader, material_library=self.material_library, color=color)
            
        if self.dir_path is not None:
            self.refreshFromDirectory()
        else:
            self.onRefresh()
            
    
    
    def onRefresh(self):
        """
        Refresh shaders from selection.
        """
        self.selectedShaders = None
        self.subnets = self.checkSelectedNodes()
        files_list_per_subnet = self.findDirectory(self.subnets)
        self.refreshFromFiles(files_list_per_subnet)
        
    
    def getLibrariesShaders(self):
        scenefile = Path(hou.hipFile.path())
        if len(scenefile.parts) < 4:
            return []
        asset_path = Path(*(scenefile.parts[:-4]))
        library_path = asset_path / Path('Libraries')
        if not os.path.exists(library_path):
            return []
        
        shaders = auto.get_shaders_from_dir(library_path)
        return shaders
        
        
    def clearVBOX(self):
        """
        Clear all shaders widgets in VBoxLayout.
        """
        self.shaders.clear()
        self.shaderWidgets.clear()
        for i in range(self.vbox.count()):
            widget: QtWidgets.QWidget = self.vbox.itemAt(i).widget()
            if widget:
                widget.deleteLater()
    
    def refreshFromFiles(self, files_list_per_subnet):
        self.clearVBOX()
                
        # Get shaders from selected subnet
        self.shaders = []
        for files_list in files_list_per_subnet:
            shader = auto.get_shaders_from_filepaths(files_list)
            if shader:
                self.shaders.append(shader[0])
        
        # Get shaders from "Libraries/textures" directory
        library_shaders = self.getLibrariesShaders()
        for lib_shader in library_shaders:
            can_be_added = True
            for shader in self.shaders:
                if lib_shader.name == shader.name:
                    can_be_added = False
            if can_be_added:
                self.shaders.append(lib_shader)
              
        # if self.selectedShaders is not None and self.shaders:
        #     for i, _ in enumerate(self.selectedShaders):
        #         if not len(files_list_per_subnet[i]):
        #             self.selectedShaders.pop(i)
        #     for i, _ in enumerate(self.selectedShaders):
        #         self.shaders[i].name = self.selectedShaders[i]
                
        self.shaderWidgets: ShaderWidget = []
        
        self.initializeShaderWidgets()
        self.setupShaderWidgets()
        
                
    def refreshFromDirectory(self):
        """
        Refresh shader list from self.dir_path.
        """
        
        self.clearVBOX()
        
        self.shaders = auto.get_shaders_from_dir(self.dir_path)
        self.shaderWidgets: ShaderWidget = []
        
        self.initializeShaderWidgets()
        self.setupShaderWidgets()
    
    def onOpenDirectory(self):
        """
        Ask the user to open a directory and parse shader from it.
        """
        
        # Start directoy will be current working directory
        start_directory = "$HIP"
        
        # Ask user where to parse maps
        dir_path = hou.ui.selectFile(
            start_directory=start_directory,
            title="Select a directory with maps",
            file_type=hou.fileType.Directory,
            default_value = "")

        # Check if the path lead to a directory
        if not os.path.isdir(dir_path):
            hlog.pinfo("Selection is not a directory.")
            hou.ui.displayMessage("Selection is not a directory.")
            return
        else:
            hlog.pdebug(f"Opening director:\n{dir_path}")
            self.dir_path = dir_path
            self.refreshFromDirectory()
            
    
    def closeEvent(self, event):
        """
        Event made to unlink this widget from houdini when closed.
        """
        
        self.setParent(None)
        return super().closeEvent(event)     
        
        
def showUI():
    """
    Method called to display autoconnect UI.
    """
    if not QT_FOUND:
        hou.ui.displayMessage(
            "Error: No QT Found",
            severity=hou.severityType.Error
        )
        return
    
    dialog = AutoConnectUI(material_library=None)
    if not dialog.initialized:
        return
    dialog.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
    dialog.show()