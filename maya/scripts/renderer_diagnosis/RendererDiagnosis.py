import os
import sys
import tempfile
from enum import Enum

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from functools import partial
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import maya.OpenMaya as OpenMaya

import pymel.core as pm

from common.utils import *
from common.Prefs import *

sys.path.append(r"R:\pipeline\networkInstall\arnold\SDK\Arnold-7.1.4.2-windows")
from arnold import *

# ######################################################################################################################

_FILE_NAME_PREFS = "renderer_diagnosis"
_NAME_TEMP_FILE = "renderer_diagnosis_export.ass"

_GRADIENT_COLOR = [
    (0.0, 100, 255, 65),
    (0.33, 255, 220, 0),
    (0.66, 226, 80, 0),
    (1, 120, 0, 0)
]


# ######################################################################################################################

class ListSort:
    def __init__(self, index, order):
        """
        Contructor
        :param index
        :param order
        """
        self.__index = index
        self.__order = order

    def get_index(self):
        """
        Getter of the index in the Table
        :return: index
        """
        return self.__index

    def get_order(self):
        """
        Getter of the order of the sort (True: Ascending, False: Descending)
        :return: order
        """
        return self.__order

    def set_index(self, index):
        """
        Setter of the index
        :param index
        :return:
        """
        self.__index = index

    def set_order(self, order):
        """
        Setter of the order
        :param order
        :return:
        """
        self.__order = order

    def toggle_order(self):
        """
        Toggle the state of the order
        :return:
        """
        self.__order = not self.__order


class ElementPolygon:
    def __init__(self, name, path, polygons=0):
        """
        Constructor
        :param name
        :param path
        :param polygons
        """
        self.__name = name
        self.__polygons = polygons
        self.__path = path
        self.__maya_obj = None
        self.__subdivisions = None
        self.__children = []

    def add_child(self, key, path):
        """
        Add a child with the given key or retrieve an existent one
        :param key
        :param path
        :return: child created
        """
        for child in self.__children:
            if child.get_name() == key:
                return child
        item = ElementPolygon(key, path)
        self.__children.append(item)
        return item

    def set_polygons(self, polygons):
        """
        Setter of the polygons count
        :param polygons
        :return:
        """
        self.__polygons = polygons

    def set_maya_obj(self, maya_obj):
        """
        Setter of the maya object linked
        :param maya_obj
        :return:
        """
        self.__maya_obj = maya_obj

    def set_subdivisions(self, subdivisions):
        """
        Setter of the subdivisions
        :param subdivisions
        :return:
        """
        self.__subdivisions = subdivisions

    def get_polygons(self):
        """
        Getter of the polygons count
        :return: polygons count
        """
        return self.__polygons

    def get_subdivisions(self):
        """
        Getter of the subdivisions
        :return: subdivisions
        """
        return self.__subdivisions

    def get_maya_objs(self):
        """
        Getter of the maya objects linked. If it doesn't have a maya object linked, find all maya objects of children
        :return: maya objects
        """
        if self.__maya_obj is None:
            arr_maya_objs = []
            for child in self.__children:
                arr_maya_objs.extend(child.get_maya_objs())
            return arr_maya_objs
        return [self.__maya_obj]

    def get_name(self):
        """
        Getter of the name
        :return: name
        """
        return self.__name

    def get_path(self):
        """
        Getter of the path
        :return: path
        """
        return self.__path

    def get_children(self):
        """
        Getter of the children
        :return: children
        """
        return self.__children

    def sort_children(self):
        """
        Sort the children accordingly to their polygons count
        :return:
        """
        self.__children = sorted(self.__children, key=lambda el: el.get_polygons(), reverse=True)


class RendererDiagnosis(QDialog):
    @staticmethod
    def val_to_color(max_val, val):
        """
        Convert a value to a color according to a gradient and the max value
        :param max_val
        :param val
        :return: color RGB
        """
        if val == 0:
            gradient_val = _GRADIENT_COLOR[0]
            return gradient_val[1], gradient_val[2], gradient_val[3]
        frac = val / max_val
        nb_val_gradient = len(_GRADIENT_COLOR)
        index = None
        for i in range(nb_val_gradient - 1, -1, -1):
            if _GRADIENT_COLOR[i][0] < frac:
                index = i
                break
        if index is None: return 0, 0, 0
        val_gradient_min = _GRADIENT_COLOR[index]
        val_gradient_max = _GRADIENT_COLOR[index + 1]
        frac_min = val_gradient_min[0]
        frac_max = val_gradient_max[0]
        frac_adapted = (frac - frac_min) * (1 / (frac_max - frac_min))
        one_minus_frac = 1 - frac_adapted
        r = val_gradient_min[1] * one_minus_frac + val_gradient_max[1] * frac_adapted
        g = val_gradient_min[2] * one_minus_frac + val_gradient_max[2] * frac_adapted
        b = val_gradient_min[3] * one_minus_frac + val_gradient_max[3] * frac_adapted
        return r, g, b

    @staticmethod
    def format_val(val):
        """
        Beautify a value. Example :
        761852943 -> 7.6M
        9435 -> 9.4K
        217 -> 217
        :param val
        :return: beautified value
        """
        if val >= 1000000:
            # More than 1000000 -> _._M
            return str(round(val / 1000000, 1)) + "M"
        elif val >= 1000:
            # More than 1000 -> _._K
            return str(round(val / 1000, 1)) + "K"
        else:
            # Else display the value
            return str(val)

    @staticmethod
    def __set_dcc_for_standins():
        """
        Set a constant to all standins to retrieve the right maya object after diagnose
        :return:
        """
        standins = pm.ls(type="aiStandIn")
        for standin in standins:
            if not pm.objExists(standin + ".mtoa_constant_renderer_diagnosis_dcc"):
                pm.addAttr(standin, longName="mtoa_constant_renderer_diagnosis_dcc", dataType="string")
            pm.setAttr(standin + ".mtoa_constant_renderer_diagnosis_dcc", standin.name())

    def __init__(self, prnt=wrapInstance(int(omui.MQtUtil.mainWindow()), QWidget)):
        super(RendererDiagnosis, self).__init__(prnt)
        AiBegin()

        # Common Preferences (common preferences on all tools)
        self.__common_prefs = Prefs()
        # Preferences for this tool
        self.__prefs = Prefs(_FILE_NAME_PREFS)

        # Model attributes
        self.__temp_path = (tempfile.gettempdir() + "/" + _NAME_TEMP_FILE).replace("\\", "/")
        self.__dict_obj_poly = {}
        self.__tree_obj_poly = None
        self.__list_obj_poly = []
        self.__standins_auto_instance = []
        self.__hidden_objects = []
        self.__diagnose_hidden_element = False
        self.__list_sort = ListSort(3, True)

        # UI attributes
        self.__ui_font = QFont("Segoe UI", 10)
        self.__ui_width = 1350
        self.__ui_height = 700
        self.__ui_min_width = 800
        self.__ui_min_height = 200
        self.__ui_pos = QDesktopWidget().availableGeometry().center() - QPoint(self.__ui_width, self.__ui_height) / 2

        self.__retrieve_prefs()

        # name the window
        self.setWindowTitle("Renderer Diagnosis")
        # make the window a "tool" in Maya's eyes so that it stays on top when you click off
        self.setWindowFlags(QtCore.Qt.Tool)
        # Makes the object get deleted from memory, not just hidden, when it is closed.
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Create the layout, linking it to actions and refresh the display
        self.__create_ui()
        self.__refresh_ui()

    def __save_prefs(self):
        """
        Save preferences
        :return:
        """
        size = self.size()
        self.__prefs["window_size"] = {"width": size.width(), "height": size.height()}
        pos = self.pos()
        self.__prefs["window_pos"] = {"x": pos.x(), "y": pos.y()}
        self.__prefs["diagnose_hidden_element"] = self.__diagnose_hidden_element
        self.__prefs["list_sort"] = {"index": self.__list_sort.get_index(), "order":self.__list_sort.get_order()}

    def __retrieve_prefs(self):
        """
        Retrieve preferences
        :return:
        """
        if "window_size" in self.__prefs:
            size = self.__prefs["window_size"]
            self.__ui_width = size["width"]
            self.__ui_height = size["height"]

        if "window_pos" in self.__prefs:
            pos = self.__prefs["window_pos"]
            self.__ui_pos = QPoint(pos["x"], pos["y"])

        if "diagnose_hidden_element" in self.__prefs:
            self.__diagnose_hidden_element = self.__prefs["diagnose_hidden_element"]

        if "list_sort" in self.__prefs:
            list_sort_data = self.__prefs["list_sort"]
            self.__list_sort.set_index(list_sort_data["index"])
            self.__list_sort.set_order(list_sort_data["order"])

    def hideEvent(self, arg__1: QCloseEvent) -> None:
        """
        Save Prefs
        :return:
        """
        self.__save_prefs()

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
        main_lyt.setContentsMargins(5, 12, 5, 7)
        self.setLayout(main_lyt)

        # Button layout
        btn_lyt = QHBoxLayout()
        btn_lyt.setAlignment(Qt.AlignCenter)
        btn_lyt.setContentsMargins(6, 6, 6, 3)
        main_lyt.addLayout(btn_lyt)

        # Diagnose scene button
        self.__ui_diagnose_scene_btn = QPushButton("Diagnose scene")
        self.__ui_diagnose_scene_btn.clicked.connect(self.__diagnose)
        self.__ui_diagnose_scene_btn.setStyleSheet("padding:8px 25px")
        btn_lyt.addWidget(self.__ui_diagnose_scene_btn)

        # Diagnose selection button
        self.__ui_diagnose_selection_btn = QPushButton("Diagnose selection")
        self.__ui_diagnose_selection_btn.clicked.connect(partial(self.__diagnose, True))
        self.__ui_diagnose_selection_btn.setStyleSheet("padding:8px 25px")
        btn_lyt.addWidget(self.__ui_diagnose_selection_btn)

        # Hidden element checkbox
        self.__ui_hidden_element_cb = QCheckBox("Diagnose hidden element")
        self.__ui_hidden_element_cb.stateChanged.connect(self.__on_diagnose_hidden_element_checked)
        btn_lyt.addWidget(self.__ui_hidden_element_cb)

        # Grid Layout
        content_lyt = QGridLayout()
        main_lyt.addLayout(content_lyt, 1)

        content_lyt.addWidget(QLabel("Hierarchy"), 0, 0, alignment=Qt.AlignCenter)
        content_lyt.addWidget(QLabel("List"), 0, 1, alignment=Qt.AlignCenter)
        content_lyt.setColumnStretch(0, 2)
        content_lyt.setColumnStretch(1, 3)

        # Hierarchy
        self.__ui_tree_polygons = QtWidgets.QTreeWidget()
        self.__ui_tree_polygons.setColumnCount(3)
        self.__ui_tree_polygons.setAlternatingRowColors(True)
        self.__ui_tree_polygons.setHeaderLabels(["Element", "Complexity", "Poly"])
        self.__ui_tree_polygons.setFont(self.__ui_font)
        header = self.__ui_tree_polygons.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.__ui_tree_polygons.itemSelectionChanged.connect(self.__on_tree_item_selected)
        content_lyt.addWidget(self.__ui_tree_polygons, 1, 0)

        # List
        self.__ui_list_polygons = QTableWidget(0, 5)
        self.__ui_list_polygons.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.__ui_list_polygons.verticalHeader().hide()
        self.__ui_list_polygons.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__ui_list_polygons.setSelectionMode(QAbstractItemView.SingleSelection)
        self.__ui_list_polygons.setHorizontalHeaderLabels(
            ["Element", "Subdiv", "Dist x Poly", "Complexity", "Poly"])
        self.__ui_list_polygons.setShowGrid(False)
        self.__ui_list_polygons.setAlternatingRowColors(True)
        self.__ui_list_polygons.setFont(self.__ui_font)
        horizontal_header = self.__ui_list_polygons.horizontalHeader()
        horizontal_header.sectionClicked.connect(self.__on_clicked_header_list)
        horizontal_header.setSortIndicatorShown(True)
        horizontal_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        horizontal_header.setSectionResizeMode(0, QHeaderView.Stretch)
        self.__ui_list_polygons.setEditTriggers(QTableWidget.NoEditTriggers)
        self.__ui_list_polygons.itemSelectionChanged.connect(self.__on_list_item_selected)
        content_lyt.addWidget(self.__ui_list_polygons, 1, 1)

        # Linear Gradient
        linear_gradient_lyt = QHBoxLayout()
        linear_gradient_lyt.setAlignment(Qt.AlignCenter)
        linear_gradient_lyt.setSpacing(15)
        linear_gradient_lyt.setContentsMargins(10, 10, 10, 10)
        self.__ui_linear_gradient = QWidget()
        self.__ui_linear_gradient.setFixedHeight(8)
        self.__ui_linear_gradient.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        linear_gradient_lyt.addWidget(QLabel("High"))
        linear_gradient_lyt.addWidget(self.__ui_linear_gradient)
        linear_gradient_lyt.addWidget(QLabel("Low"))
        main_lyt.addLayout(linear_gradient_lyt)

    def __refresh_ui(self):
        """
        Refresh the ui according to the model attribute
        :return:
        """
        self.__ui_hidden_element_cb.setChecked(self.__diagnose_hidden_element)
        self.__refresh_gradient()
        self.__refresh_list_sorting()
        self.__refresh_list()
        self.__refresh_tree()

    def __refresh_gradient(self):
        """
        Refresh the gradient
        :return:
        """
        css = "background: qlineargradient(x1:0, y1:0.5, x2:1, y2:0.5,"
        for stop, r, g, b in _GRADIENT_COLOR:
            css += "stop:" + str(1 - stop) + " rgb(" + str(r) + "," + str(g) + "," + str(b) + "),"
        css += ");"
        self.__ui_linear_gradient.setStyleSheet(css)

    def __refresh_list_sorting(self):
        """
        Refresh the sorting of the list
        :return:
        """
        self.__ui_list_polygons.horizontalHeader().setSortIndicator(
            self.__list_sort.get_index(), Qt.AscendingOrder if self.__list_sort.get_order() else Qt.DescendingOrder)

    def __refresh_list(self):
        """
        Refresh the list displaying elements sorted by size
        :return:
        """
        if self.__tree_obj_poly is None: return
        scene_polygons = self.__tree_obj_poly.get_polygons()
        self.__ui_list_polygons.setRowCount(0)
        list_obj_polygons = sorted(list(self.__dict_obj_poly.items()), key=lambda el: el[1]["polygons"], reverse=True)
        list_sorted_dist_poly = sorted(list(self.__dict_obj_poly.items()),
                                             key=lambda el: (el[1]["dist_poly"],el[1]["polygons"]), reverse=True)
        row_index = 0
        max_poly = list_obj_polygons[0][1]["polygons"] if len(list_obj_polygons) > 0 else 0
        max_dist_poly = list_sorted_dist_poly[0][1]["dist_poly"] if len(
            list_sorted_dist_poly) > 0 else 0

        index_sort = self.__list_sort.get_index()
        order_sort = self.__list_sort.get_order()

        if index_sort == 1:
            used_list = sorted(list(self.__dict_obj_poly.items()),
                               key=lambda el: (el[1]["subdiv"],el[1]["polygons"]), reverse=order_sort)
        elif index_sort==2:
            used_list = list_sorted_dist_poly if order_sort else \
                sorted(list(self.__dict_obj_poly.items()),
                       key=lambda el: (el[1]["dist_poly"],el[1]["polygons"]))
        else:
            used_list = list_obj_polygons if order_sort else \
                sorted(list(self.__dict_obj_poly.items()), key=lambda el: el[1]["polygons"])

        for node_name, data in used_list:
            polygons = data["polygons"]
            dist_poly = data["dist_poly"]
            subdivisions = data["subdiv"]
            self.__ui_list_polygons.insertRow(row_index)
            # Element
            elem_item = QTableWidgetItem("  " + node_name)
            elem_item.setToolTip(node_name)
            elem_item.setData(Qt.UserRole, (node_name, data["maya_obj"]))
            self.__ui_list_polygons.setItem(row_index, 0, elem_item)
            # Subdivisions
            if subdivisions is not None:
                subdivisions_item = QTableWidgetItem(str(subdivisions))
                subdivisions_item.setTextAlignment(Qt.AlignCenter)
                self.__ui_list_polygons.setItem(row_index, 1, subdivisions_item)
            # Dist/Poly
            if dist_poly is not None:
                r, g, b = RendererDiagnosis.val_to_color(max_dist_poly, dist_poly)
                dist_poly_widget_wrapper = QWidget()
                dist_poly_widget = QWidget()
                dist_poly_widget.setStyleSheet("background-color:rgb(" + str(r) + "," + str(g) + "," + str(b) + ");")
                dist_poly_widget.setFixedSize(QSize(12, 12))
                dist_poly_layout = QHBoxLayout()
                dist_poly_layout.setContentsMargins(0, 0, 20, 0)
                dist_poly_layout.addStretch()
                dist_poly_layout.addWidget(QLabel(str(round(dist_poly * 100 / max_dist_poly, 1)) + "%"))
                dist_poly_layout.addWidget(dist_poly_widget)
                dist_poly_widget_wrapper.setLayout(dist_poly_layout)
                self.__ui_list_polygons.setCellWidget(row_index, 2, dist_poly_widget_wrapper)
            # Complexity
            r, g, b = RendererDiagnosis.val_to_color(max_poly, polygons)
            icon_widget_wrapper = QWidget()
            icon_widget = QWidget()
            icon_widget.setStyleSheet("background-color:rgb(" + str(r) + "," + str(g) + "," + str(b) + ");")
            icon_widget.setFixedSize(QSize(12, 12))
            icon_layout = QHBoxLayout()
            icon_layout.setContentsMargins(0, 0, 20, 0)
            icon_layout.addStretch()
            icon_layout.addWidget(QLabel(str(round(polygons * 100 / scene_polygons, 1)) + "%"))
            icon_layout.addWidget(icon_widget)
            icon_widget_wrapper.setLayout(icon_layout)
            self.__ui_list_polygons.setCellWidget(row_index, 3, icon_widget_wrapper)
            # Polygons
            polygons_item = QTableWidgetItem(RendererDiagnosis.format_val(polygons))
            polygons_item.setTextAlignment(Qt.AlignCenter)
            self.__ui_list_polygons.setItem(row_index, 4, polygons_item)
            row_index += 1

    def __refresh_tree(self):
        """
        Refresh the tree displaying the hierarchy of the scene with their size
        :return:
        """

        if self.__tree_obj_poly is None: return
        scene_polygons = self.__tree_obj_poly.get_polygons()
        stylesheet_padding = "padding-right:20px; padding-top:5px; padding-bottom:5px"

        def __build_ui_tree_polygons(ui_item, tree_item, expand=False):
            """
            Create recursively the ui tree. if an element is expanded then the parent has to be expanded
            :param ui_item
            :param tree_item
            :param expand: force expand
            :return: expand
            """
            children = tree_item.get_children()
            expand |= len(children) > 1
            for child in tree_item.get_children():
                polygons = child.get_polygons()
                path = child.get_path()
                ui_child = QtWidgets.QTreeWidgetItem(ui_item)
                ui_child.setToolTip(0, path)
                ui_child.setData(0, Qt.UserRole, (path, child.get_maya_objs()))
                expand |= __build_ui_tree_polygons(ui_child, child)

                ui_child.setFont(0, self.__ui_font)
                # Name
                ui_child.setText(0, child.get_name())
                # Color
                r, g, b = RendererDiagnosis.val_to_color(scene_polygons, polygons)
                icon_widget_wrapper = QWidget()
                icon_widget = QWidget()
                icon_widget.setStyleSheet("background-color:rgb(" + str(r) + "," + str(g) + "," + str(b) + ");")
                icon_widget.setFixedSize(QSize(12, 12))
                icon_layout = QHBoxLayout()
                icon_layout.setContentsMargins(0, 0, 20, 0)
                icon_layout.addStretch()
                icon_layout.addWidget(QLabel(str(round(polygons * 100 / scene_polygons, 1)) + "%"))
                icon_layout.addWidget(icon_widget)
                icon_widget_wrapper.setLayout(icon_layout)
                self.__ui_tree_polygons.setItemWidget(ui_child, 1, icon_widget_wrapper)
                # Number of polygons
                label_polygons = QLabel(RendererDiagnosis.format_val(polygons))
                label_polygons.setStyleSheet(stylesheet_padding)
                label_polygons.setFont(self.__ui_font)
                label_polygons.setAlignment(Qt.AlignRight)
                self.__ui_tree_polygons.setItemWidget(ui_child, 2, label_polygons)
            ui_item.setExpanded(expand)
            return expand

        self.__ui_tree_polygons.clear()
        if self.__tree_obj_poly is None: return
        # Root
        root = QtWidgets.QTreeWidgetItem(self.__ui_tree_polygons)
        root.setData(0, Qt.UserRole, (self.__tree_obj_poly.get_path(), self.__tree_obj_poly.get_maya_objs()))
        root.setFont(0, self.__ui_font)
        root.setText(0, self.__tree_obj_poly.get_name())
        label_polygons = QLabel(RendererDiagnosis.format_val(scene_polygons))
        label_polygons.setStyleSheet(stylesheet_padding)
        label_polygons.setAlignment(Qt.AlignRight)
        label_polygons.setFont(self.__ui_font)
        self.__ui_tree_polygons.setItemWidget(root, 2, label_polygons)
        self.__ui_tree_polygons.addTopLevelItem(root)
        __build_ui_tree_polygons(root, self.__tree_obj_poly, True)

    def __on_diagnose_hidden_element_checked(self, state):
        """
        Retrieve the checkbox state
        :param state
        :return:
        """
        self.__diagnose_hidden_element = state != Qt.Unchecked

    def __on_clicked_header_list(self, index):
        """
        Change the sorting of the list on click on the header of the list
        :param index: index column
        :return:
        """
        if index in [1,2,3,4]:
            if self.__list_sort.get_index() == index:
                self.__list_sort.toggle_order()
            else:
                self.__list_sort.set_index(index)
                self.__list_sort.set_order(True)
            self.__refresh_list()
        self.__refresh_list_sorting()

    def __fix_auto_instancing(self):
        """
        Set the autoInstancing attribute to False because it doesn't works with export with expandProcedural
        :return:
        """
        standins = pm.ls(type="aiStandIn")
        self.__standins_auto_instance.clear()
        for standin in standins:
            if standin.useAutoInstancing.get() == 1:
                self.__standins_auto_instance.append(standin)
                standin.useAutoInstancing.set(0)

    def __restore_auto_instancing(self):
        """
        Restore the autoInstancing
        :return:
        """
        for standin in self.__standins_auto_instance:
            standin.useAutoInstancing.set(1)
        self.__standins_auto_instance.clear()

    def __show_objects(self):
        """
        Show all the objects in the DAG
        :return:
        """
        self.__hidden_objects.clear()
        all_objects = pm.ls(dagObjects=True)
        for obj in all_objects:
            if not obj.visibility.get():
                self.__hidden_objects.append(obj)
                obj.visibility.set(1)

    def __restore_hidden_objects(self):
        """
        Hide the objects that were hidden
        :return:
        """
        for obj in self.__hidden_objects:
            obj.visibility.set(0)
        self.__hidden_objects.clear()

    def __export_ass(self, selected=False):
        """
        Export the scene in a tempfile ass to retrieve all the informations we need
        :return:
        """
        diagnose_hidden_objects = self.__diagnose_hidden_element
        if diagnose_hidden_objects: self.__show_objects()
        if selected:
            pm.select(pm.ls(selection=True, dagObjects=True))
        else:
            pm.select(pm.ls(dagObjects=True))

        command_1 = 'file -force -options "-mask 6399;-lightLinks 1;-shadowLinks 1;-expandProcedurals;-fullPath" ' \
                    '-type "ASS Export" -pr -es "' + self.__temp_path + '"; '
        command_2 = 'arnoldExportAss -f "' + self.__temp_path + '" -s -boundingBox -mask 6399 -lightLinks 1 -shadowLinks 1 ' \
                                                                '-expandProcedurals -fullPath -cam perspShape; '
        self.__fix_auto_instancing()
        try:
            pm.mel.eval(command_1)
            pm.mel.eval(command_2)
        except:
            os.remove(self.__temp_path)
            print_warning("Error while exporting as ASS file")
        self.__restore_auto_instancing()
        if diagnose_hidden_objects: self.__restore_hidden_objects()
        pm.select([])

    def __on_list_item_selected(self):
        """
        On selection in the table changed
        :return:
        """
        rows = self.__ui_list_polygons.selectionModel().selectedRows()
        if len(rows) > 0:
            path, maya_objs = self.__ui_list_polygons.item(rows[0].row(), 0).data(Qt.UserRole)
            pm.select(maya_objs)
            QApplication.clipboard().setText(path)

    def __on_tree_item_selected(self):
        """
        On selection in the tree changed select the maya object and copy the path to the clipboard
        :return:
        """
        items = self.__ui_tree_polygons.selectedItems()
        if len(items) > 0:
            path, maya_objs = items[0].data(0, Qt.UserRole)
            pm.select(maya_objs)
            QApplication.clipboard().setText(path)

    def __retrieve_polygons(self):
        """
        Retrieve some datas in the ASS file exported. Retrieve the polygon count and the subdivision count for each
        polymesh and curves
        :return:
        """
        self.__dict_obj_poly.clear()

        camera_trsf = None
        cameras = pm.ls(cameras=True)
        for camera in cameras:
            if pm.getAttr(camera + '.renderable'):
                camera_trsf = camera.getTransform()
                break

        AiASSLoad(self.__temp_path)
        univ = AiUniverseGetNodeIterator(AI_NODE_SHAPE)
        while not AiNodeIteratorFinished(univ):
            node = AiNodeIteratorGetNext(univ)
            node_name = AiNodeGetName(node)
            if not node_name: continue
            renderer_diagnosis_dcc = AiNodeGetStr(node, "renderer_diagnosis_dcc")
            is_polymesh_standin = AiNodeIs(node, "polymesh") and len(renderer_diagnosis_dcc) > 0
            is_polymesh_mesh = AiNodeIs(node, "polymesh")
            is_curves = AiNodeIs(node, "curves") and len(renderer_diagnosis_dcc) > 0
            if is_polymesh_standin or is_polymesh_mesh:
                nsides = AiArrayGetNumElements(AiNodeGetArray(node, "nsides").contents)
            elif is_curves:
                nsides = round(AiArrayGetNumElements(AiNodeGetArray(node, "num_points").contents) / 3.5)
            else:
                continue

            subdiv_iterations = AiNodeGetInt(node, "subdiv_iterations")
            if subdiv_iterations > 0:
                nsides = nsides * pow(4, subdiv_iterations)
            else:
                subdiv_iterations = None

            if is_polymesh_standin or is_curves:
                parent = pm.PyNode(renderer_diagnosis_dcc).getParent() \
                    if pm.objExists(renderer_diagnosis_dcc) else None
                parent_name = "/" + parent.name() if parent is not None else ""
            else:
                parent_request = pm.ls(node_name.replace("/", "|"))
                parent = parent_request[0].getParent() if len(parent_request) > 0 else None
                parent_name = ""

            dist_poly = None
            if camera_trsf is not None and parent is not None:
                dist = (camera_trsf.getBoundingBox(space="world").center() - parent.getBoundingBox(space="world").center()).length()
                dist_poly = dist * nsides

            if is_curves:
                name = "/".join((parent_name + node_name).split("/"))
            else:
                name = "/".join((parent_name + node_name).split("/")[:-1])

            self.__dict_obj_poly[name] = {
                "polygons": nsides,
                "maya_obj": parent,
                "subdiv": subdiv_iterations,
                "dist_poly": dist_poly
            }
        AiNodeIteratorDestroy(univ)
        AiEnd()
        AiBegin()

    def __build_tree_objects_polygons(self):
        """
        Create the tree structure of ElementPolygon
        :return:
        """

        def __insert_in_tree(tree, obj_path_array, maya_object, polygon_count, nb_subdivisions):
            """
            insert in the tree the hierarchy for one leaf
            :param tree
            :param obj_path_array
            :param maya_object
            :param polygon_count
            :param nb_subdivisions
            :return:
            """
            path = ""
            for key in obj_path_array:
                path += "/" + key
                tree = tree.add_child(key, path)
            tree.set_polygons(polygon_count)
            tree.set_maya_obj(maya_object)
            tree.set_subdivisions(nb_subdivisions)

        self.__tree_obj_poly = ElementPolygon("root", "/")
        for obj_path, data in self.__dict_obj_poly.items():
            objs = obj_path.split('/')[1:]
            __insert_in_tree(self.__tree_obj_poly, objs, data["maya_obj"], data["polygons"], data["subdiv"])

    def __compute_polygons_parent(self):
        """
        Compute values for nodes in the tree that aren't leaves
        :return:
        """

        def __compute_polygons(item):
            """
            Recursive function to compute values for the whole tree
            :param item:
            :return:
            """
            children = item.get_children()
            nb_children = len(children)
            if nb_children == 0:
                return
            polygons = 0
            for child in item.get_children():
                __compute_polygons(child)
                polygons += child.get_polygons()
            item.set_polygons(polygons)

        __compute_polygons(self.__tree_obj_poly)

    def __sort_tree_recursive(self):
        """
        Sort each children array for each node in the tree
        :return:
        """

        def __sort_tree_recursive_aux(elem):
            """
            Recursive function to sort the whole tree
            :param elem:
            :return:
            """
            elem.sort_children()
            for child in elem.get_children():
                __sort_tree_recursive_aux(child)

        __sort_tree_recursive_aux(self.__tree_obj_poly)

    def __diagnose(self, selected=False):
        """
        Execute the diagnosis
        :param selected: diagnose only selected
        :return:
        """
        self.__set_dcc_for_standins()
        self.__export_ass(selected)
        self.__retrieve_polygons()
        self.__build_tree_objects_polygons()
        self.__compute_polygons_parent()
        self.__sort_tree_recursive()
        self.__refresh_list()
        self.__refresh_tree()
