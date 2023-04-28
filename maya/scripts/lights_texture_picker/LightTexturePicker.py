import math
import os
from collections import namedtuple
from os import listdir
from os.path import isfile, join

import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.mel as mel

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from shiboken2 import wrapInstance

# Table code taken from here:
# https://www.pythonguis.com/faq/file-image-browser-app-with-thumbnails/

# Light Texture type for the model
light_texture = namedtuple("light_texture", "id title image")


# Delegate class for the TableView
class LightTextureDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, padding=5):
        super().__init__()
        self.__padding = padding

    def paint(self, painter, option, index):
        # data is our light_texture object
        data = index.model().data(index, QtCore.Qt.DisplayRole)
        if data is None:
            return

        width = option.rect.width() - self.__padding * 2
        height = option.rect.height() - self.__padding * 2

        # option.rect holds the area we are painting on the widget (our table cell)
        # scale our pixmap to fit
        scaled = data.image.scaled(
            width,
            height,
            aspectRatioMode=QtCore.Qt.KeepAspectRatio,
        )
        # Position in the middle of the area.
        x = self.__padding + (width - scaled.width()) / 2
        y = self.__padding + (height - scaled.height()) / 2

        painter.drawImage(option.rect.x() + x, option.rect.y() + y, scaled)

    def sizeHint(self, option, index):
        # All items the same size.
        return QtCore.QSize(100, 100)


# Model class for the TableView
class LightTextureModel(QtCore.QAbstractTableModel):

    def __init__(self, column=4, todos=None):
        super().__init__()
        # .data holds our data for display, as a list of light_texture objects.
        self.light_textures = []
        self.__column = column

    def data(self, index, role=None):
        try:
            # print(index.row() * self.__column + index.column())
            data = self.light_textures[index.row() * self.__column + index.column()]
        except IndexError:
            # Incomplete last row.
            return

        if role == QtCore.Qt.DisplayRole:
            return data  # Pass the data to our delegate to draw.

        if role == QtCore.Qt.ToolTipRole:
            return data.title

    def columnCount(self, index=None):
        return self.__column

    def rowCount(self, index=None):
        n_items = len(self.light_textures)
        return math.ceil(n_items / self.__column)


class LightTexturePicker(QtWidgets.QDialog):
    TEXTURE_PATH = "R:\\lib\\hdri_light_v2\\jpg"

    # Retrieve the selected light or create one
    def __init__(self, parent=wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)):
        super(LightTexturePicker, self).__init__(parent)

        # Model attributes
        self.__lights_list = []
        self.__lights_selected = []
        self.__texture = None

        # UI attributes
        self.__ui_lights_list = []
        self.__ui_light_list_widget = None
        self.__ui_texture_table_widget = None
        self.__ui_btn_remove_texture = None
        self.__ui_btn_validate = None

        # Setup model attributes
        self.__retrieve_lights()
        self.__retrieve_selected_lights()

        # name the window
        self.setWindowTitle("Light Texture Picker")
        # make the window a "tool" in Maya's eyes so that it stays on top when you click off
        self.setWindowFlags(QtCore.Qt.Tool)
        # Makes the object get deleted from memory, not just hidden, when it is closed.
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Create the layout and linking it to actions
        self.__create_layout()
        self.__link_actions()

        # Refresh the button
        self.__refresh_enable_button()

    def is_valid(self):
        return len(self.__lights_selected) > 0 and self.__texture is not None

    # If lights are selected we take them
    def __retrieve_selected_lights(self):
        self.__lights_selected = cmds.ls(sl=True, type=["light"] + cmds.listNodeTypes("light"), dag=True)

    def __retrieve_lights(self):
        self.__lights_list = cmds.ls(type=["light"] + cmds.listNodeTypes("light"), dag=True)

    # Attach the texture light to the lights
    def attach_texture(self):
        if len(self.__lights_selected) > 0:
            render_node = self.__create_render_node_texture()
            for light in self.__lights_selected:
                attr_light = light + '.color'
                # Get all the connections for the color attribute of the light and disconnect them
                conns_lights = cmds.listConnections(attr_light, plugs=True, destination=False) or []
                if conns_lights:
                    for conn in conns_lights:
                        cmds.disconnectAttr(conn, attr_light)
                # Connect the new texture
                cmds.connectAttr(render_node + '.outColor', light + '.color')

    # Remove the texture of lights
    def remove_textures(self):
        for light in self.__lights_selected:
            attr_light = light + '.color'
            # Get all the connections for the color attribute of the light and disconnect them
            conns_lights = cmds.listConnections(attr_light, plugs=True, destination=False) or []
            if conns_lights:
                for conn in conns_lights:
                    cmds.disconnectAttr(conn, attr_light)
                cmds.setAttr(attr_light, 1, 1, 1, type='double3')

            # Create a Render Node for a file

    def __create_render_node_texture(self):
        render_node = cmds.shadingNode("file", asTexture=True, asUtility=True)
        #SWITCH TO TX
        parentDir =os.path.dirname(os.path.dirname(self.__texture))
        filename = os.path.basename(self.__texture)
        filenameTX =  os.path.splitext(filename)[0]+".tx"
        pathTX= os.path.join(parentDir,filenameTX)

        cmds.setAttr(render_node + '.fileTextureName', pathTX,
                     type="string")
        return render_node

    def __select_lights(self):
        cmds.select(clear=True)
        for light in self.__lights_selected:
            cmds.select(light, add=True)

    # Create the layout
    def __create_layout(self):
        # Reinit attributes of the UI
        self.__ui_lights_list = []
        self.__ui_texture_list = None
        self.__ui_light_list_widget = None
        self.__ui_texture_table_widget = None
        self.__ui_btn_remove_texture = None
        self.__ui_btn_validate = None

        # Some aesthetic value
        bias = 20
        size_btn = QtCore.QSize(180, 40)

        # Main Layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        self.setLayout(main_layout)

        # Horizontal Layout 1
        horizontal_layout_1 = QtWidgets.QHBoxLayout()
        main_layout.addLayout(horizontal_layout_1)

        # List Lights
        self.__ui_light_list_widget = QtWidgets.QListWidget()
        self.__ui_light_list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        # Create Items
        for light in self.__lights_list:
            item = QtWidgets.QListWidgetItem(light)
            self.__ui_lights_list.append(item)
            self.__ui_light_list_widget.addItem(item)
        # Set the right items selected
        for light in self.__lights_selected:
            for light_item in self.__ui_lights_list:
                if light == light_item.text():
                    light_item.setSelected(True)
        # Resize
        width = self.__ui_light_list_widget.sizeHintForColumn(0) + bias
        self.__ui_light_list_widget.setMinimumWidth(width)
        self.__ui_light_list_widget.setMaximumWidth(width)
        self.__ui_light_list_widget.adjustSize()
        horizontal_layout_1.addWidget(self.__ui_light_list_widget)

        # List Texture
        self.__ui_texture_table_widget = QtWidgets.QTableView()
        self.__ui_texture_table_widget.horizontalHeader().hide()
        self.__ui_texture_table_widget.verticalHeader().hide()
        self.__ui_texture_table_widget.setGridStyle(QtCore.Qt.NoPen)
        self.__ui_texture_table_widget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        # Create Delegate and Model
        delegate = LightTextureDelegate(padding=5)
        model = LightTextureModel(column=4)
        self.__ui_texture_table_widget.setItemDelegate(delegate)
        self.__ui_texture_table_widget.setModel(model)
        for n, f in enumerate(listdir(self.TEXTURE_PATH)):
            filename = join(self.TEXTURE_PATH, f)
            filename_without_ext = os.path.splitext(filename)[0]
            if isfile(filename):
                image = QtGui.QImage(filename_without_ext)
                item = light_texture(n, filename, image)
                model.light_textures.append(item)
        model.layoutChanged.emit()
        # Resize
        self.__ui_texture_table_widget.resizeRowsToContents()
        self.__ui_texture_table_widget.resizeColumnsToContents()
        width = model.columnCount() * self.__ui_texture_table_widget.sizeHintForColumn(0) + bias
        height = min(model.rowCount() * self.__ui_texture_table_widget.sizeHintForRow(0) + bias, 600)
        self.__ui_texture_table_widget.setMinimumWidth(width)
        self.__ui_texture_table_widget.setMinimumHeight(height)
        horizontal_layout_1.addWidget(self.__ui_texture_table_widget)

        # Horizontal Layout 2
        horizontal_layout_2 = QtWidgets.QHBoxLayout()
        horizontal_layout_2.setContentsMargins(5, 5, 5, 5)
        main_layout.addLayout(horizontal_layout_2)

        # Button Remove Texture
        self.__ui_btn_remove_texture = QtWidgets.QPushButton("Remove texture")
        self.__ui_btn_remove_texture.setFixedSize(size_btn)
        horizontal_layout_2.addWidget(self.__ui_btn_remove_texture)

        # Button Validate
        self.__ui_btn_validate = QtWidgets.QPushButton("Validate")
        self.__ui_btn_validate.setFixedSize(size_btn)
        horizontal_layout_2.addWidget(self.__ui_btn_validate)

    # Link action to elements in the UI
    def __link_actions(self):
        self.__ui_light_list_widget.itemSelectionChanged.connect(self.__on_light_selection_changed)
        self.__ui_texture_table_widget.selectionModel().selectionChanged.connect(self.__on_texture_selection_changed)
        self.__ui_btn_remove_texture.clicked.connect(self.__on_click_remove_texture)
        self.__ui_btn_validate.clicked.connect(self.__on_clic_validate_texture_choice)

    # Update the list of lights selected when the selection change in the light list
    def __on_light_selection_changed(self):
        self.__lights_selected = []
        cmds.select(clear=True)
        for list_item_widget in self.__ui_light_list_widget.selectedItems():
            light = list_item_widget.text()
            self.__lights_selected.append(light)
            cmds.select(light, add=True)
        self.__refresh_enable_button()

    # Update the texture selected
    def __on_texture_selection_changed(self):
        model = self.__ui_texture_table_widget.model()
        column_count = model.columnCount()
        index = self.__ui_texture_table_widget.currentIndex()
        index_computed = column_count * index.row() + index.column()
        if index_computed < len(model.light_textures):
            self.__texture = model.light_textures[index_computed].title
        else:
            self.__texture = None
            self.__ui_texture_table_widget.clearSelection()
        self.__refresh_enable_button()

    # Event function when click on remove texture
    def __on_click_remove_texture(self):
        for light in self.__lights_selected:
            attr_light = light + '.color'
            # Get all the connections for the color attribute of the light
            conns_lights = cmds.listConnections(attr_light, plugs=True, destination=False) or []
            if conns_lights:
                self.remove_textures()
                self.__refresh_enable_button()
                break

    # Event function when click on validate
    def __on_clic_validate_texture_choice(self):
        print(self.__lights_selected)
        print(self.__texture)
        if self.is_valid():
            self.attach_texture()
            self.__select_lights()
            self.__refresh_enable_button()

    # Refresh buttons
    def __refresh_enable_button(self):
        self.__ui_btn_validate.setEnabled(self.is_valid())
        lights_selected_empty = len(self.__lights_selected) <= 0
        remove_texture = False
        for light in self.__lights_selected:
            attr_light = light + '.color'
            # Get all the connections for the color attribute of the light
            conns_lights = cmds.listConnections(attr_light, plugs=True, destination=False) or []
            if conns_lights:
                remove_texture = True
                break
        self.__ui_btn_remove_texture.setEnabled(remove_texture)
        self.__ui_texture_table_widget.setEnabled(not lights_selected_empty)

    def print(self):
        print("lights_list", end="")
        print(self.__lights_list)
        print("lights_selected", end="")
        print(self.__lights_selected)
        print("textures", end="")
        print(self.__textures)


if __name__ == '__main__':
    ltp = LightTexturePicker()
    ltp.show()
