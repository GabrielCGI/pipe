import os
import re
import glob
import hou

from enum import Enum
from pathlib import Path
from functools import partial

from . import houdinilog as hlog
from . import auto
from . import shader as sh
from . import map as mp

try:
    from .qt import QtCore, QtWidgets

    QT_FOUND = True
except ImportError:
    QT_FOUND = False


QSS_STYLESHEET_PATH = os.path.join(
    os.path.dirname(__file__), "ressource", "autoconnect_stylesheet.qss"
)
DEFAULT_VERSION_VALUE = "----"


class MapState(Enum):
    CAN_BE_UPDATED = "can_be_updated"
    NEW = "new"
    ALREADY_UPDATED = "already_uptead"

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
        self,
        mapName: str,
        current_map: str = DEFAULT_VERSION_VALUE,
        new_map: str = DEFAULT_VERSION_VALUE,
        listVersion: list[str] = [DEFAULT_VERSION_VALUE],
        versioning=False,
        parent=None,
    ):
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
        self.current_map = current_map
        self.new_map = new_map
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
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )

        self.listVersion.sort()
        self.latestVersion = self.listVersion[-1]

        self.versions: list[str] = self.listVersion
        self.versionsLabel = QtWidgets.QLabel()
        self.setVersionText(self.current_map, self.new_map)
        if self.state == MapState.ALREADY_UPDATED:
            self.checkbox.setChecked(False)

        hbox.addWidget(self.spacer)
        hbox.addWidget(self.versionsLabel)

        self.versionComboBox = QtWidgets.QComboBox()
        if self.versioning:
            self.versionComboBox.addItems(self.listVersion)
            self.versionComboBox.setCurrentText(self.new_map)
            self.versionComboBox.currentTextChanged.connect(self.onVersionChanged)
        else:
            self.versionComboBox.addItem(DEFAULT_VERSION_VALUE)
            self.versionComboBox.setCurrentText(DEFAULT_VERSION_VALUE)
            self.versionComboBox.setDisabled(True)
        hbox.addWidget(self.versionComboBox)

        self.setLayout(hbox)

    def setVersionText(self, old_version, version):
        """
        Update text depending of map state and selected version.

        Args:
            old_version (str): Selected map version.
            version (str): Last version available.
        """

        if old_version != DEFAULT_VERSION_VALUE:
            if old_version == self.latestVersion:
                self.state = MapState.ALREADY_UPDATED
                if self.versioning:
                    self.versionsLabel.setText(
                        f"{self.state.description()}" + f"{version}"
                    )
                else:
                    self.versionsLabel.setText(self.state.description())
            else:
                self.state = MapState.CAN_BE_UPDATED
                if self.versioning:
                    self.versionsLabel.setText(
                        f"{self.state.description()}" + f"{old_version} --> {version}"
                    )
        else:
            self.state = MapState.NEW
            if self.versioning:
                self.versionsLabel.setText(f"{self.state.description()}" + f"{version}")
            else:
                self.versionsLabel.setText(self.state.description())
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
        self.setVersionText(self.current_map, currentVersion)

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

    def __init__(
        self,
        shaderName: str,
        shader: sh.Shader,
        maps: list[MapWidget],
        versioning: bool = False,
        color: hou.Color = None,
        parent=None,
    ):
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
        self.shader = shader
        self.maps = maps
        self.versioning = versioning
        self.color = color

        self.mapWidgets: list[MapWidget] = []
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
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        hbox.addWidget(self.spacer)

        self.colorWidget = QtWidgets.QWidget()
        self.spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        self.colorWidget.setMinimumWidth(300)
        self.colorWidget.setObjectName("colorWidget")
        hbox.addWidget(self.colorWidget)

        self.versionComboBox = QtWidgets.QComboBox()
        self.versionComboBox.currentTextChanged.connect(self.onVersionChanged)
        if not self.versioning:
            self.versionComboBox.addItem(DEFAULT_VERSION_VALUE)
            self.versionComboBox.setCurrentText(DEFAULT_VERSION_VALUE)
            self.versionComboBox.setDisabled(True)
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
            rgb_css = (
                f"rgb({self.color[0] * 255},"
                + f" {self.color[1] * 255}, {self.color[2] * 255})"
            )
            background_color = f"background: {rgb_css};"
            self.setStyleSheet(
                f"QWidget#colorWidget {{{background_color}}}"
                + f"QLabel#shaderName {{color: {rgb_css};}}"
            )

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
        versions = [DEFAULT_VERSION_VALUE]
        for mapWidget in self.mapWidgets:
            map_version = mapWidget.getVersions()
            if map_version is not None:
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

        if not everyStateNew and not everyStateAlreadyUpdated:
            self.currentState = MapState.CAN_BE_UPDATED
            self.stateLabel.setText(f"{self.currentState.description()}")
        elif everyStateNew:
            self.currentState = MapState.NEW
            self.stateLabel.setText(f"{self.currentState.description()}")
        elif everyStateAlreadyUpdated:
            self.currentState = MapState.ALREADY_UPDATED
            self.stateLabel.setText(f"{self.currentState.description()}")
        else:
            # Default state of new (but cannot happens)
            self.currentState = MapState.NEW
            self.stateLabel.setText(f"{self.currentState.description()}")

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
        if not self.mainItem.isExpanded():
            self.setFixedHeight(rowHeight)
        else:
            self.setFixedHeight(rowHeight * (len(self.mapWidgets) + 1))

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
        if currentVersion != DEFAULT_VERSION_VALUE:
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
            itemWidget.checkbox.setChecked(not itemWidget.checkbox.isChecked())

    def setCheckAll(self, on: bool):
        for map in self.mapWidgets:
            map.checkbox.setChecked(on)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjustSize()


class AutoConnectUI(QtWidgets.QMainWindow):
    def __init__(self, material_library=None, parent=None):
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
        self.setWindowTitle("Autoconnect")

        self.initializeStyleSheet()
        self.initializeCentralWidget()
        self.initializeToolbar()

        self.material_library = material_library
        self.dir_path = None
        self.selectedShaders = []
        self.shaders = []
        self.shaderWidgets: list[ShaderWidget] = []

        self.refreshShaders()

        self.initialized = self.material_library is not None

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
        self.scrollarea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.central = QtWidgets.QWidget()
        self.central.setMinimumWidth(600)
        self.central.setObjectName("centralWidget")

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setAlignment(QtCore.Qt.AlignTop)

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
        self.refreshButton.clicked.connect(self.refreshShaders)
        self.toolbar.addWidget(self.refreshButton)

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        self.toolbar.addWidget(spacer)

        self.applyButton = QtWidgets.QPushButton()
        self.applyButton.setText("Apply")
        self.applyButton.clicked.connect(self.onCreate)
        self.toolbar.addWidget(self.applyButton)

        self.toolbar.setMovable(False)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.toolbar)

    def refreshShaders(self):
        """
        Refresh shaders from selection.
        """
        self.selectedShaders = []
        subnets = self.checkSelectedNodes()
        mats_by_subnet = self.parseMatsBySubnets(subnets)
        self.refreshFromFiles(mats_by_subnet)

    def initializeShaderWidgets(self):
        """
        Initialized shader widget from existing sh.Shader object.
        """
        self.shaderWidgets.clear()
        for shader in self.shaders:
            listMapWidgets = []
            shader.setLatestMap()
            existingSubnet = auto.get_existing_subnet(
                self.material_library, shader.name
            )

            existingShader: sh.Shader = None
            subnet_color = None
            if existingSubnet is not None:
                existingShader = auto.get_shader_from_subnet(existingSubnet)
                subnet_color = existingSubnet.color().rgb()

            # initialize unversionned map
            for map in shader.unversionned_map:
                current_map: mp.Map = existingShader.existMaps(map, versionned=False)
                if current_map is None:
                    current_map = DEFAULT_VERSION_VALUE
                mapWidget = MapWidget(
                    mapName=map.name,
                    current_map=current_map.name,
                    new_map=map.name,
                    listVersion=[map.name],
                    versioning=False,
                )
                listMapWidgets.append(mapWidget)

            # initialize versionned map with the latest available
            for map in shader.latest_maps:
                listVersion = []
                for mapVersion in shader.allVersionsMaps[map.name]:
                    listVersion.append(mapVersion.version)
                old_version = DEFAULT_VERSION_VALUE
                if existingShader is not None:
                    existingMap = existingShader.existMaps(map, versionned=True)
                    if existingMap is not None:
                        old_version = existingShader.allVersionsMaps[existingMap][
                            0
                        ].version
                mapWidget = MapWidget(
                    mapName=map.name,
                    current_map=old_version,
                    new_map=map.version,
                    listVersion=listVersion,
                    versioning=True,
                )
                listMapWidgets.append(mapWidget)
            versioning = len(shader.latest_maps)
            shaderWidget = ShaderWidget(
                shaderName=shader.name,
                shader=shader,
                maps=listMapWidgets,
                versioning=versioning,
                color=subnet_color,
            )
            self.shaderWidgets.append(shaderWidget)

    def setupShaderWidgets(self):
        """
        Add shader widget to vbox layout.
        """

        self.initializeShaderWidgets()
        new_shader = []
        for shaderWidget in self.shaderWidgets:
            if shaderWidget.color is None:
                new_shader.append(shaderWidget)

        for i, shaderWidget in enumerate(self.shaderWidgets):
            hbox = QtWidgets.QHBoxLayout()

            labelShader = QtWidgets.QLabel(f"<h4>Shader {i + 1}:</h4>")
            hbox.addWidget(labelShader)

            labelName = QtWidgets.QLabel(f"<h4>{shaderWidget.shaderName}</h4>")

            color = None
            if shaderWidget in new_shader:
                r, g, b = auto.getColor(i, len(self.shaderWidgets))
                color = hou.Color(r, g, b).rgb()
                shaderWidget.setColor(color)
            else:
                color = shaderWidget.color
            if color is not None:
                labelName.setStyleSheet(
                    f"color: rgb({color[0] * 255}, {color[1] * 255}, {color[2] * 255})"
                )

            hbox.addWidget(labelName)

            select_button = QtWidgets.QPushButton("Select All")
            select_button.clicked.connect(
                partial(self.shaderWidgets[i].setCheckAll, True)
            )
            hbox.addWidget(select_button)

            deselect_button = QtWidgets.QPushButton("Deselect All")
            deselect_button.clicked.connect(
                partial(self.shaderWidgets[i].setCheckAll, False)
            )
            hbox.addWidget(deselect_button)

            widget = QtWidgets.QWidget()
            widget.setLayout(hbox)
            self.vbox.addWidget(widget)
            widget.setSizePolicy(
                QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
            )

            self.vbox.addWidget(shaderWidget)

    def readShaders(self):
        """
        Read shader widgets as sh.Shader to be able to build them.
        """

        self.shadersToUpdate = []
        for shaderWidget in self.shaderWidgets:
            if not shaderWidget.checkbox.isChecked():
                continue
            shader = shaderWidget.shader
            self.shadersToUpdate.append(shader)
            anyMapChecked = False
            shader.selected_maps.clear()
            if shaderWidget.versioning:
                shader_version = shaderWidget.versionComboBox.currentText()
                toggleSpecificVersion = shader_version != DEFAULT_VERSION_VALUE
                for mapWidget in shaderWidget.mapWidgets:
                    if not mapWidget.checkbox.isChecked():
                        continue
                    anyMapChecked = True
                    version = None
                    if toggleSpecificVersion:
                        version = shader_version
                    else:
                        version = mapWidget.versionComboBox.currentText()
                    listVersion: list[mp.VersionMap] = shader.allVersionsMaps[
                        mapWidget.mapNameLabel.text()
                    ]
                    for map in listVersion:
                        if map.version == version:
                            shader.selected_maps.append(map)
                            break
            else:
                for mapWidget in shaderWidget.mapWidgets:
                    if mapWidget.checkbox.isChecked():
                        continue
                    anyMapChecked = True
                    for map in shader.latest_maps:
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
        selectedNodes = hou.selectedNodes()
        if len(selectedNodes):
            subnets = []
            if selectedNodes[0].type().name() == "materiallibrary":
                self.material_library = selectedNodes[0]
                subnets += self.material_library.children()

                self.selectedShaders = []
                for subnet in self.material_library.children():
                    self.selectedShaders.append(subnet.name())
                return subnets
            elif selectedNodes[0].parent().type().name() == "materiallibrary":
                self.material_library = selectedNodes[0].parent()
                subnets += selectedNodes

                self.selectedShaders = []
                for node in selectedNodes:
                    self.selectedShaders.append(node.name())
                return subnets
        hlog.pinfo("Please selected a material library or some shaders.")
        hou.ui.displayMessage("Please selected a material library or some shaders")
        return []

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

    def parseMatsBySubnets(self, subnets: list[hou.VopNode]):
        """
        Find every files candidates for an update based on shader already
        present in a material library.

        Warning: Multiple usages of recursive glob search, potentially
        computationnal heavy.
        """
        maps_by_subnets = {}
        for subnet in subnets:
            for node in subnet.children():
                if node.type().name() == "mtlximage":
                    map_path = node.parm("file").eval()
                    if map_path is not None:
                        map_list: list = maps_by_subnets.setdefault(subnet.name(), [])
                        map_list.append(map_path)

        udim_c = re.compile(".<UDIM>")

        for subnet in maps_by_subnets:
            parsed_maps = []
            for map_path in maps_by_subnets.get(subnet, []):
                versionMatch = mp.VERSION_PATTERN_COMPILE.search(map_path)
                if versionMatch is None:
                    continue
                versionSpan = versionMatch.span()
                globpath = map_path[: versionSpan[0]] + "*" + map_path[versionSpan[1] :]
                udimMatch = udim_c.search(globpath)
                if udimMatch:
                    udimSpan = udimMatch.span()
                    globpath = globpath[: udimSpan[0]] + "*" + globpath[udimSpan[1] :]
                parsed_maps += glob.glob(pathname=globpath)
            maps_by_subnets[subnet] = list(set(parsed_maps))

        return maps_by_subnets

    def refreshFromFiles(self, maps_by_subnets: dict):
        self.clearVBOX()

        # Get shaders from selected subnet
        self.shaders: list[sh.Shader] = []
        for subnet in maps_by_subnets:
            map_paths: list = maps_by_subnets.get(subnet, [])
            shader = auto.get_shader(subnet, map_paths)
            if not shader.isEmpty():
                self.shaders.append(shader)

        # Get shaders from "Libraries/textures" directory
        library_shaders = self.getLibrariesShaders()
        for lib_shader in library_shaders:
            can_be_added = True
            for shaders in self.shaders:
                if lib_shader.name == shaders.name:
                    can_be_added = False
            if can_be_added:
                self.shaders.append(lib_shader)

        if len(self.selectedShaders) and self.shaders:
            unused_shaders = []
            for shader in self.selectedShaders:
                if shader not in maps_by_subnets.keys():
                    unused_shaders.append(shader)
            for shader in unused_shaders:
                self.selectedShaders.remove(shader)

        self.shaderWidgets: list[ShaderWidget] = []
        self.setupShaderWidgets()

    def getLibrariesShaders(self):
        scenefile = Path(hou.hipFile.path())
        if len(scenefile.parts) < 4:
            return []
        asset_path = Path(*(scenefile.parts[:-4]))
        library_path = asset_path / Path("Libraries")
        if not os.path.exists(library_path):
            return []

        shaders = auto.get_shaders_from_dir(library_path)
        return shaders

    def refreshFromDirectory(self):
        """
        Refresh shader list from self.dir_path.
        """

        self.clearVBOX()

        self.shaders = auto.get_shaders_from_dir(self.dir_path)
        self.shaderWidgets: list[ShaderWidget] = []
        self.setupShaderWidgets()

    def onCreate(self):
        """
        Slot to create selected shaders.
        """
        self.readShaders()
        if not auto.ask_confirmation(self.shadersToUpdate):
            return
        self.changeActivePane()
        with hou.undos.group(f"Create/Update {len(self.shadersToUpdate)} shaders"):
            for shader in self.shadersToUpdate:
                color = None
                for shaderWidget in self.shaderWidgets:
                    if shader.name == shaderWidget.mapNameLabel.text():
                        color = hou.Color(shaderWidget.color)
                auto.create_shader_network(
                    shader, material_library=self.material_library, color=color
                )
        if self.dir_path is not None:
            self.refreshFromDirectory()
        else:
            self.refreshShaders()

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
            default_value="",
        )

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
        hou.ui.displayMessage("Error: No QT Found", severity=hou.severityType.Error)
        return

    dialog = AutoConnectUI()
    if not dialog.initialized:
        return
    dialog.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
    dialog.show()
