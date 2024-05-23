import os
from functools import partial

import sys

import pymel.core as pm
import maya.OpenMayaUI as omui
maya_version = pm.about(version=True)
if maya_version.startswith("2022"):
    # Using PySide2 for Maya 2022
    from PySide2 import QtCore, QtGui, QtWidgets
    from PySide2.QtWidgets import *
    from PySide2.QtCore import *
    from PySide2.QtGui import *
elif maya_version.startswith("2025"):
    # Using PySide6 for Maya 2025
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtGui import *


if maya_version.startswith("2022"):
    # Using Shiboken2 for Maya 2022
    from shiboken2 import wrapInstance
elif maya_version.startswith("2025"):
    # Using Shiboken6 for Maya 2025
    from shiboken6 import wrapInstance
from common.utils import *

from common.Prefs import *

import maya.OpenMaya as OpenMaya

from .ABCImportAsset import *

# ######################################################################################################################

_FILE_NAME_PREFS = "abc_import"


# ######################################################################################################################


class ABCImport(QDialog):

    @staticmethod
    def get_aiStandIn_shape():
        # Get the current selection
        selection = pm.selected()

        if not selection:
            return None

        # Check if selection is aiStandIn or its transform
        for sel in selection:
            if isinstance(sel, pm.nodetypes.AiStandIn):
                return sel
            elif sel.getShape() and isinstance(sel.getShape(), pm.nodetypes.AiStandIn):
                return sel.getShape()

        # If not found, check parent of the first selected object
        parent = selection[0].getParent()
        if parent:
            parent_shape = parent.getShape()
            if isinstance(parent_shape, pm.nodetypes.AiStandIn):
                return parent_shape
            else:
                gparent = parent[0].getParent()
                if gparent:
                    parent_shape = gparent.getShape()
                    if isinstance(parent_shape, pm.nodetypes.AiStandIn):
                        return parent_shape



        return None

    @staticmethod
    def __get_abc_parent_dir(max_recursion):
        """
        Get the directory parent of the abc folders
        :param max_recursion
        :return:
        """
        folder_name_target = ["abc", "abc_fur"]
        def check_dir_recursive(count, dirpath):
            for child_dirname in os.listdir(dirpath):
                child_dirpath = os.path.join(dirpath, child_dirname)
                if os.path.isdir(child_dirpath) and child_dirname in folder_name_target:
                    return dirpath.replace("\\", "/")
            if count >= max_recursion:
                return None
            next_dirpath = os.path.dirname(dirpath)
            if not os.path.exists(next_dirpath):
                return None
            return check_dir_recursive(count + 1, next_dirpath)

        standin_shape = ABCImport.get_aiStandIn_shape()
        if standin_shape:
            dso = standin_shape.dso.get()
            parts = dso.split('/')
            dir =  '/'.join(parts[:3] + [parts[3].split('/')[0]])
            if os.path.exists(dir):
                return dir


        scene_name = pm.sceneName()
        if len(scene_name) > 0:
            dirpath = os.path.dirname(scene_name)
            abc_parent_dir = check_dir_recursive(1, dirpath)
        else:
            abc_parent_dir = None
        return abc_parent_dir

    @staticmethod
    def __is_correct_folder(folder):
        """
        Test if a folder is correct to be a container of abcs
        :param folder
        :return:
        """
        if not os.path.exists(folder):
            return False
        if ABCImport.__is_parent_abc_folder(folder):
            return True
        if ABCImport.__is_abc_folder(folder):
            return True
        if ABCImport.__is_abc_fur_folder(folder):
            return True
        return False

    @staticmethod
    def __is_abc_folder(folder):
        """
        Test whether the folder is an abc folder or not
        :param folder
        :return:
        """
        return re.match(r".*[/\\]abc[/\\]?$", folder)

    @staticmethod
    def __is_abc_fur_folder(folder):
        """
        Test whether the folder is an abc_fur folder or not
        :param folder:
        :return:
        """
        return re.match(r".*[/\\]abc_fur[/\\]?$", folder)

    @staticmethod
    def __is_parent_abc_folder(folder):
        """
        Test whether the folder is a parent of an abc folder or an abc_fur folder or not
        :param folder:
        :return:
        """
        for d in os.listdir(folder):
            if os.path.isdir(os.path.join(folder, d)):
                if d in ["abc", "abc_fur"]:
                    return True
        return False

    def __init__(self, directory=None, prnt=wrapInstance(int(omui.MQtUtil.mainWindow()), QWidget)):
        super(ABCImport, self).__init__(prnt)

        # Common Preferences (common preferences on all tools)
        self.__common_prefs = Prefs()
        # Preferences for this tool
        self.__prefs = Prefs(_FILE_NAME_PREFS)

        if directory and os.path.isdir(directory):
            self.__folder_path = directory.replace("\\", "/")
        else:
            dirname = ABCImport.__get_abc_parent_dir(4)
            self.__folder_path = dirname if dirname is not None else ""

        self.__update_uvs_shaders = True
        self.__abcs = []
        self.__selected_abcs = []

        self.__retrieve_current_project_dir()
        self.__look_factory = LookFactory(self.__current_project_dir)
        self.__retrieve_abcs()

        # UI attributes
        self.__ui_width = 600
        self.__ui_height = 400
        self.__ui_min_width = 400
        self.__ui_min_height = 250
        self.__ui_pos = QDesktopWidget().availableGeometry().center() - QPoint(self.__ui_width, self.__ui_height) / 2

        self.__retrieve_prefs()

        # name the window
        self.setWindowTitle("ABC Import")
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

    def hideEvent(self, arg__1: QCloseEvent) -> None:
        """
        Save preferences
        :return:
        """
        self.__save_prefs()

    def __retrieve_current_project_dir(self):
        """
        Retrieve the current project dir specified in the Illogic maya launcher
        :return:
        """
        self.__current_project_dir = os.getenv("CURRENT_PROJECT_DIR")
        if self.__current_project_dir is None:
            self.__stop_and_display_error()

    def __stop_and_display_error(self):
        """
        Delete the window and show an error message
        :return:
        """
        self.deleteLater()
        msg = QMessageBox()
        msg.setWindowTitle("Error current project directory not found")
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Current project directory not found")
        msg.setInformativeText("Current project directory has not been found. You should use an Illogic Maya Launcher")
        msg.exec_()

    def __create_ui(self):
        """
        Create the ui
        :return:
        """
        # Reinit attributes of the UI
        self.setMinimumSize(self.__ui_min_width, self.__ui_min_height)
        self.resize(self.__ui_width, self.__ui_height)
        self.move(self.__ui_pos)

        asset_dir = os.path.join(os.path.dirname(__file__), "assets")
        browse_icon_path = os.path.join(asset_dir, "browse.png")
        import_icon_path = os.path.join(asset_dir, "import.png")

        # Main Layout
        main_lyt = QVBoxLayout()
        main_lyt.setContentsMargins(8, 12, 8, 12)
        main_lyt.setSpacing(7)
        self.setLayout(main_lyt)

        # Folder selection layout
        folder_lyt = QHBoxLayout()
        main_lyt.addLayout(folder_lyt)
        self.__ui_folder_path = QLineEdit(self.__folder_path)
        self.__ui_folder_path.setFixedHeight(27)
        self.__ui_folder_path.textChanged.connect(self.__on_folder_changed)
        folder_lyt.addWidget(self.__ui_folder_path)

        browse_btn = QPushButton()
        browse_btn.setIconSize(QtCore.QSize(18, 18))
        browse_btn.setFixedSize(QtCore.QSize(24, 24))
        browse_btn.setIcon(QIcon(QPixmap(browse_icon_path)))
        browse_btn.clicked.connect(partial(self.__browse_folder))
        browse_btn.setToolTip("Browse a folder of ABCS")
        folder_lyt.addWidget(browse_btn)

        import_btn = QPushButton()
        import_btn.setIconSize(QtCore.QSize(18, 18))
        import_btn.setFixedSize(QtCore.QSize(24, 24))
        import_btn.setIcon(QIcon(QPixmap(import_icon_path)))
        import_btn.clicked.connect(partial(self.__browse_import_abc_file))
        import_btn.setToolTip("Browse an abc and import it")
        folder_lyt.addWidget(import_btn)

        # Asset Table
        self.__ui_abcs_table = QTableWidget(0, 5)
        self.__ui_abcs_table.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.__ui_abcs_table.verticalHeader().hide()
        self.__ui_abcs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__ui_abcs_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.__ui_abcs_table.setHorizontalHeaderLabels(
            ["State", "Asset name", "Actual version", "Import version", "Look"])
        horizontal_header = self.__ui_abcs_table.horizontalHeader()
        horizontal_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        horizontal_header.setSectionResizeMode(1, QHeaderView.Stretch)
        horizontal_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        horizontal_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        horizontal_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.__ui_abcs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.__ui_abcs_table.itemSelectionChanged.connect(self.__on_abcs_selection_changed)
        main_lyt.addWidget(self.__ui_abcs_table)

        # Update UV and Shader checkbox
        self.__ui_update_uvs_shaders = QCheckBox("Set last Look")
        self.__ui_update_uvs_shaders.setChecked(self.__update_uvs_shaders)
        self.__ui_update_uvs_shaders.stateChanged.connect(self.__on_checked_update_uvs_shaders)
        main_lyt.addWidget(self.__ui_update_uvs_shaders, 0, Qt.AlignHCenter)

        # Submit Import button
        self.__ui_import_btn = QPushButton("Import or Update selection")
        self.__ui_import_btn.clicked.connect(self.__import_update_selected_abcs)
        main_lyt.addWidget(self.__ui_import_btn)

        # Submit Import button
        self.__ui_replace_btn = QPushButton("Replace by last selected")
        self.__ui_replace_btn.clicked.connect(self.__ui_replace_btn_clicked)
        main_lyt.addWidget(self.__ui_replace_btn)
    def __refresh_ui(self):
        """
        Refresh the ui according to the model attribute
        :return:
        """
        self.__refresh_btn()
        self.__refresh_table()

    def __refresh_btn(self):
        """
        Refresh the button import
        :return:
        """
        nb_abcs_selected = len(self.__selected_abcs)
        enabled = True
        tooltip = ""
        if nb_abcs_selected == 0:
            enabled = False
            tooltip = "Select atleast one abc to import or update"
        elif not self.__is_correct_folder(self.__folder_path):
            enabled = False
            tooltip = "The export folder must be named a parent folder of a folder named \"abc\" or \"abc_fur\""
        self.__ui_import_btn.setEnabled(enabled)
        self.__ui_import_btn.setToolTip(tooltip)

    def __refresh_table(self):
        """
        Refresh the table
        :return:
        """
        selected_abcs = [abc.get_name() for abc in self.__selected_abcs]

        asset_dir = os.path.dirname(__file__) + "/assets/"

        self.__ui_abcs_table.setRowCount(0)
        row_index = 0
        selected_rows = []
        for abc in self.__abcs:
            # Get model data
            name = abc.get_name()
            anim_versions = abc.get_versions()
            anim_import_version = abc.get_import_path()
            anim_actual_version = abc.get_actual_version()

            self.__ui_abcs_table.insertRow(row_index)

            if name in selected_abcs:
                selected_rows.append(row_index)

            # Get if the abc is NEW (2),  Present and out of date (1) or Present and Up to date (0)
            if anim_actual_version is None:
                state = ABCState.New
            else:
                if int(os.path.basename(anim_actual_version)) < int(os.path.basename(anim_versions[0])):
                    state = ABCState.OutOfDate
                else:
                    state = ABCState.UpToDate

            # Icon State
            icon_widget = QLabel()
            icon_widget.setFixedSize(QSize(25, 25))
            icon_widget.setScaledContents(True)
            if state == ABCState.UpToDate:
                tooltip = "Up to date"
            elif state == ABCState.OutOfDate:
                tooltip = "Out of date"
            else:
                tooltip = "New"
            pixmap = QPixmap(asset_dir + abc.get_icon_filename(state))
            icon_widget.setPixmap(pixmap)
            icon_widget.setToolTip(tooltip)

            # State
            container_icon_widget = QWidget()
            layout_container_icon_widget = QVBoxLayout(container_icon_widget)
            layout_container_icon_widget.setContentsMargins(0, 0, 0, 0)
            layout_container_icon_widget.addWidget(icon_widget)
            layout_container_icon_widget.setAlignment(Qt.AlignCenter)
            container_icon_widget.setLayout(layout_container_icon_widget)
            self.__ui_abcs_table.setCellWidget(row_index, 0, container_icon_widget)

            # Name
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, abc)
            self.__ui_abcs_table.setItem(row_index, 1, name_item)
            if state == ABCState.New:
                self.__ui_abcs_table.setSpan(row_index, 1, 1, 2)

            # Actual version
            if state != ABCState.New:
                version_item = QTableWidgetItem(abc.get_actual_version())
                version_item.setData(Qt.UserRole, abc)
                version_item.setTextAlignment(Qt.AlignCenter)
                self.__ui_abcs_table.setItem(row_index, 2, version_item)

            # Import version
            import_version_combobox = QComboBox()
            import_version_combobox.setStyleSheet(".QComboBox{margin:2px; padding:3px}")
            self.__ui_abcs_table.setCellWidget(row_index, 3, import_version_combobox)
            for v in anim_versions:
                import_version_combobox.addItem(os.path.basename(v), v)
            import_version_combobox.currentIndexChanged.connect(partial(self.__on_version_combobox_changed, row_index))
            if anim_import_version is not None:
                import_version_combobox.setCurrentText(os.path.basename(anim_import_version))

            # Action
            if state != ABCState.New:
                if not abc.is_look_up_to_date():
                    print("ABC LOOK NOT UP TO DATE")
                    pixmap = QPixmap(asset_dir + abc.get_icon_filename(state))
                    print(asset_dir + abc.get_icon_filename(state))
                    look_icon_widget = QLabel()
                    look_icon_widget.setFixedSize(QSize(22, 22))
                    look_icon_widget.setScaledContents(True)
                    look_icon_widget.setPixmap(pixmap)
                    look_icon_widget.setToolTip("Look out of date")
                    pixmap = QPixmap(asset_dir + "warning.png")
                    look_icon_widget.setPixmap(pixmap)
                    container_look_icon_widget = QWidget()
                    layout_container_look_icon_widget = QVBoxLayout(container_look_icon_widget)
                    layout_container_look_icon_widget.setContentsMargins(0, 0, 0, 0)
                    layout_container_look_icon_widget.addWidget(look_icon_widget)
                    layout_container_look_icon_widget.setAlignment(Qt.AlignCenter)
                    container_look_icon_widget.setLayout(layout_container_look_icon_widget)
                    self.__ui_abcs_table.setCellWidget(row_index, 4, container_look_icon_widget)

            row_index += 1

        # Select the previous selected rows
        self.__ui_abcs_table.setSelectionMode(QAbstractItemView.MultiSelection)
        for row_index in selected_rows:
            self.__ui_abcs_table.selectRow(row_index)
        self.__ui_abcs_table.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def __ui_replace_btn_clicked(self):

        transforms = pm.ls(selection=True, type='transform')
        ai_standins = [node for transform in transforms for node in transform.listRelatives(allDescendents=True, type='aiStandIn')]
        if ai_standins:
            last_selected_dso = ai_standins[-1].dso.get()
            for standin in ai_standins:
                # Replace the 'dso' attribute with that of the last selected aiStandIn
                standin.dso.set(last_selected_dso)
        else:
            pm.warning('No aiStandIn nodes found in the selection hierarchy.')


    def __browse_folder(self):
        """
        Browse a new folder path
        :return:
        """
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select ABC Directory", self.__folder_path)
        if ABCImport.__is_correct_folder(folder_path) and folder_path != self.__folder_path:
            self.__ui_folder_path.setText(folder_path)

    def __browse_import_abc_file(self):
        """
        Browse an abc file and import it
        :return:
        """
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, "Select ABC File to Import", self.__folder_path, "ABC (*.abc)")[0]
        match = re.match(r"^.*[/\\](?:(.*)(?:_[a-zA-Z]+(?:\.[0-9]+)?)|(.*))\.abc$", file_path)
        if match:
            if match.group(1) is None:
                asset = ABCImportAnim(match.group(2), self.__current_project_dir, self.__look_factory)
            else:
                asset = ABCImportFur(match.group(1), self.__current_project_dir, self.__look_factory)
            self.__retrieve_alone_asset_in_scene(asset)
            asset.set_import_path(os.path.dirname(file_path))
            pm.select(asset.import_update_abc(True))
            self.__retrieve_assets_in_scene()
            self.__refresh_ui()

    def __on_selection_changed(self, *args, **kwarrgs):
        """
        Refresh ui on new selection
        :return:
        """
        self.__retrieve_assets_in_scene()
        self.__refresh_ui()

    def __on_checked_update_uvs_shaders(self, state):
        """
        On check update uvs and shaders
        :param state:
        :return:
        """
        self.__update_uvs_shaders = state == 2

    def __on_folder_changed(self):
        """
        Retrieve the new folder and refresh the ui on new folder
        :return:
        """
        retrieved_text = self.__ui_folder_path.text().strip("\\/")
        if self.__folder_path != retrieved_text:
            self.__folder_path = retrieved_text
            self.__retrieve_abcs()
            self.__refresh_ui()

    def __on_abcs_selection_changed(self):
        """
        On selection in the table changed
        :return:
        """
        self.__selected_abcs.clear()
        for selected_row in self.__ui_abcs_table.selectionModel().selectedRows():
            self.__selected_abcs.append(self.__ui_abcs_table.item(selected_row.row(), 1).data(Qt.UserRole))
        self.__refresh_btn()

    def __on_version_combobox_changed(self, row_index, cb_index):
        """
        On import version changed for an abc
        :param row_index
        :param cb_index
        :return:
        """
        abc = self.__ui_abcs_table.item(row_index, 1).data(Qt.UserRole)
        version_path = self.__ui_abcs_table.cellWidget(row_index, 3).model().item(cb_index).data(Qt.UserRole)
        abc.set_import_path(version_path)

    def __retrieve_abcs(self):
        """
        Retrieve the abcs at the folder path.
        If parent folder specified, retrieves abc and abc_fur
        If only one, retrieves the one selected
        :return:
        """
        self.__abcs.clear()
        if os.path.exists(self.__folder_path):
            if ABCImport.__is_parent_abc_folder(self.__folder_path):
                self.__retrieve_assets(os.path.join(self.__folder_path, "abc"), True)
                self.__retrieve_assets(os.path.join(self.__folder_path, "abc_fur"), False)
            elif ABCImport.__is_abc_folder(self.__folder_path):
                self.__retrieve_assets(self.__folder_path, True)
            elif ABCImport.__is_abc_fur_folder(self.__folder_path):
                pass
                self.__retrieve_assets(self.__folder_path, False)
        self.__retrieve_assets_in_scene()

    def __retrieve_assets(self, folder_path, is_anim_folder):
        """
        Auxiliary method to retrieve assets in the file architecture of the folder path
        :param folder_path
        :param is_anim_folder
        :return:
        """
        folder_path = folder_path.replace("\\","/")
        if not os.path.isdir(folder_path): return
        for asset_folder in os.listdir(folder_path):
            asset_folder_path = os.path.join(folder_path, asset_folder)
            anim_versions = []
            if not os.path.isdir(asset_folder_path) or asset_folder[0:2] != "ch": continue
            for version_folder in os.listdir(asset_folder_path):
                version_folder_path = os.path.join(asset_folder_path, version_folder)
                if not os.path.isdir(version_folder_path): continue
                for abc in os.listdir(version_folder_path):
                    add = False
                    if is_anim_folder:
                        if asset_folder + ".abc" == abc:
                            add = True
                    else:
                        if re.match(r""+asset_folder+r"_fur(?:\.[0-9]+)?\.abc", abc):
                            add = True
                    if add :
                        anim_versions.append(version_folder_path)
                        break
            if len(anim_versions) < 1: continue
            if is_anim_folder:
                asset = ABCImportAnim(asset_folder, self.__current_project_dir, self.__look_factory, anim_versions)
            else:
                asset = ABCImportFur(asset_folder, self.__current_project_dir, self.__look_factory, anim_versions)
            self.__abcs.append(asset)

    def __retrieve_alone_asset_in_scene(self, abc):
        """
        Retrieve one alone asset in scene
        It can retrieve abc_fur having the abc file in the dso or
        it can retrieve abc having the abc file in the abc_layer
        :param abc
        """
        standins = pm.ls(type="aiStandIn")
        abc_name = abc.get_name()
        for standin in standins:
            # Check dso
            dso = standin.dso.get()
            if dso is not None:
                match_dso = re.match(r".*[\\/](.*_fur)(?:\.[0-9]+)?\.abc", dso, re.IGNORECASE)
                if match_dso and match_dso.group(1) == abc_name:
                    abc.set_actual_standins([standin])
                    return

            # Check abc_layer
            standin_node = pm.listRelatives(standin, parent=True)[0]
            abc_layer = standin_node.dso.get()
            if abc_layer is not None:
                abc_layer = abc_layer.replace("\\", "/")
                match_abc_layer = re.match(r".*[\\/](.*)\.abc", abc_layer, re.IGNORECASE)
                if match_abc_layer and match_abc_layer.group(1) == abc_name:
                    abc.set_actual_standins([standin])


    def __retrieve_assets_in_scene(self):
        """
        Retrieve assets in scene
        It can retrieve abc_fur having the abc file in the dso or
        it can retrieve abc having the abc file in the abc_layer
        :return:
        """
        standins = pm.ls(type="aiStandIn")
        standins_datas = {}
        if len(self.__abcs) == 0:
            return
        for standin in standins:
            added = False

            # Check dso
            dso = standin.dso.get()
            if dso is not None:
                match_dso = re.match(r".*/(.*)/([0-9]{4})/.*_[0-9]{2}_fur(?:\.[0-9]+)?\.abc", dso, re.IGNORECASE)
                if match_dso:
                    name = match_dso.group(1) + "_fur"
                    acc_standins = standins_datas[name][0] if name in standins_datas else []
                    acc_standins.append(standin)
                    standins_datas[name] = (acc_standins, match_dso.group(2))
                    added = True
            if not added:
                # Check abc_layer
                standin_node = pm.listRelatives(standin, parent=True)[0]
                abc_layer = standin_node.dso.get()
                if abc_layer is not None:
                    abc_layer = abc_layer.replace("\\", "/")
                    match_abc_layer = re.match(r".*/(.*)/([0-9]{4})/.*_[0-9]{2}\.abc", abc_layer, re.IGNORECASE)
                    if match_abc_layer:
                        name = match_abc_layer.group(1)
                        acc_standins = standins_datas[name][0] if name in standins_datas else []
                        acc_standins.append(standin)
                        standins_datas[name] = (acc_standins, match_abc_layer.group(2))

        # Make the correspondence between abcs in file architecture and abcs in scene
        for abc in self.__abcs:
            abc_name = abc.get_name()
            if abc_name in standins_datas.keys():
                abc.set_actual_standins(standins_datas[abc_name][0])
                abc.set_actual_version(standins_datas[abc_name][1])
            else:
                abc.set_actual_standins([])
                abc.set_actual_version(None)

    def __import_update_selected_abcs(self):
        """
        Import the selected abcs
        :return:
        """
        standin_nodes = []
        for abc in self.__selected_abcs:
            standin_nodes.extend(abc.import_update_abc(self.__update_uvs_shaders))
        pm.select(standin_nodes)
        self.__retrieve_assets_in_scene()
        self.__refresh_ui()
