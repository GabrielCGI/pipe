import os
import re
from functools import partial

import sys

import pymel.core as pm
import maya.OpenMayaUI as omui

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from shiboken2 import wrapInstance

from common.utils import *

from common.Prefs import *

import maya.OpenMaya as OpenMaya

# ######################################################################################################################

_FILE_NAME_PREFS = "character_publisher"


# ######################################################################################################################


class CharacterPublisher(QDialog):
    @staticmethod
    def texture_path_to_output_tx_path(texture_path, color_space, render_color_space):
        """
        Generate a path corresponding to the output tx
        :param texture_path
        :param color_space
        :param render_color_space
        :return:
        """
        texture_path = os.path.normpath(texture_path)
        dir_path, file_ext = os.path.splitext(texture_path)
        file_name = os.path.basename(dir_path)

        output_path = os.path.join(
            os.path.dirname(dir_path),
            f"{file_name}_{color_space}_{render_color_space}{file_ext}.tx"
        )
        output_path_legacy = os.path.splitext(texture_path)[0] + ".tx"

        return output_path, output_path_legacy

    @staticmethod
    def __check_color_sets(color_set_name):
        """
        Check if color sets diffferent from "Pref" exists
        :param color_set_name
        :return:
        """
        # Get the selected objects
        selected_objects = pm.selected()

        # Iterate through the selected objects
        for obj in selected_objects:
            try:
                # Get the shapes of the object and its children
                shapes = obj.getShapes(noIntermediate=True) + \
                         pm.listRelatives(obj, allDescendents=True, type='mesh', noIntermediate=True)

                # Iterate through the shapes
                for shape in shapes:
                    # Get the color sets of the shape
                    color_sets = pm.polyColorSet(shape, query=True, allColorSets=True)

                    # Check if any color sets are present
                    if not color_sets:
                        continue
                    # Iterate through the color sets
                    for color_set in color_sets:
                        # Show a pop-up window if the color set name is not the provided color set name
                        if color_set != color_set_name:
                            response = pm.confirmDialog(
                                title='Warning',
                                message="Shape '{}' has a color set named '{}' which is "
                                        "different from '{}'. Continue?".format(shape, color_set, color_set_name),
                                button=['Continue', 'Cancel'],
                                defaultButton='Continue',
                                cancelButton='Cancel',
                                dismissString='Cancel'
                            )

                            if response == 'Cancel':
                                pm.error("Aborted by user")
                                return
                            print("Color set found: {} {}".format(color_set_name, shape))
            except:
                continue

    @staticmethod
    def get_path_from_texture_node(tex_node):
        """
        Get the file path attributes from a texture node (File or image here)
        :param tex_node
        :return:
        """
        if pm.objectType(tex_node, isType="file"):
            return tex_node.fileTextureName.get()
        elif pm.objectType(tex_node, isType="aiImage"):
            return tex_node.filename.get()
        else:
            return None

    @staticmethod
    def set_path_to_texture_node(tex_node, path):
        """
        Set the file path attributes to a texture node (File or image here)
        :param tex_node
        :param path
        :return:
        """
        if pm.objectType(tex_node, isType="file"):
            tex_node.fileTextureName.set(path)
        elif pm.objectType(tex_node, isType="aiImage"):
            tex_node.filename.set(path)

    def __init__(self, prnt=wrapInstance(int(omui.MQtUtil.mainWindow()), QWidget)):
        super(CharacterPublisher, self).__init__(prnt)

        # Common Preferences (common preferences on all tools)
        self.__common_prefs = Prefs()
        # Preferences for this tool
        self.__prefs = Prefs(_FILE_NAME_PREFS)

        # Model attributes
        self.__texture_node = []
        self.__selection = []
        self.__asset_dir = ""
        self.__asset_name = None
        self.__abc_dir = ""
        self.__abc_name = ""
        self.__publish_uv = True
        self.__publish_look = True
        self.__look_name = ""
        self.__selection_callback = None

        # UI attributes
        self.__ui_width = 350
        self.__ui_height = 150
        self.__ui_min_width = 250
        self.__ui_min_height = 100
        self.__ui_pos = QDesktopWidget().availableGeometry().center() - QPoint(self.__ui_width, self.__ui_height) / 2

        self.__retrieve_prefs()

        # name the window
        self.setWindowTitle("Character Publisher")
        # make the window a "tool" in Maya's eyes so that it stays on top when you click off
        self.setWindowFlags(QtCore.Qt.Tool)
        # Makes the object get deleted from memory, not just hidden, when it is closed.
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.__retrieve_dir_and_asset_from_scene_name()
        if self.__asset_name is not None:
            self.__retrieve_datas()
            # Create the layout and refresh the display
            self.__create_ui()
            self.__refresh_ui()
            self.__add_callback()
        else:
            self.close()
            msg = QMessageBox()
            msg.setWindowTitle("Asset directory and name not found")
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Retrieving the asset directory and asset name has failed")
            msg.setInformativeText('Make sure the opened scene is good and retry')
            msg.exec_()

    def __save_prefs(self):
        """
        Save preferences
        :return:
        """
        size = self.size()
        self.__prefs["window_size"] = {"width": size.width(), "height": size.height()}
        pos = self.pos()
        self.__prefs["window_pos"] = {"x": pos.x(), "y": pos.y()}
        self.__prefs["publish_uv"] = self.__publish_uv
        self.__prefs["publish_look"] = self.__publish_look

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

        if "publish_uv" in self.__prefs:
            self.__publish_uv = self.__prefs["publish_uv"]

        if "publish_look" in self.__prefs:
            self.__publish_look = self.__prefs["publish_look"]

    def showEvent(self, arg__1: QShowEvent) -> None:
        # Nothing
        pass

    def hideEvent(self, arg__1: QCloseEvent) -> None:
        """
        Remove callbacks and save preferences
        :return:
        """
        self.__remove_callback()
        self.__save_prefs()

    def __add_callback(self):
        """
        Add callbacks
        :return:
        """
        self.__selection_callback = \
            OpenMaya.MEventMessage.addEventCallback("SelectionChanged", self.__on_selection_changed)

    def __remove_callback(self):
        """
        Remove the selection callback
        :return:
        """
        if self.__selection_callback is not None:
            OpenMaya.MMessage.removeCallback(self.__selection_callback)

    def __retrieve_dir_and_asset_from_scene_name(self):
        """
        Guess the asset directory and name from the current scene name
        :return:
        """
        scene = pm.system.sceneName()
        split = scene.split("/")
        split[0] = split[0] + "\\"
        for i, s in enumerate(reversed(split)):
            if s == "assets":
                self.__asset_dir = os.path.join(*split[0:-(i - 1)])
                self.__asset_name = split[-i]

    def __create_ui(self):
        """
        Create the ui
        :return:
        """
        # Reinit attributes of the UI
        self.setMinimumSize(self.__ui_min_width, self.__ui_min_height)
        self.resize(self.__ui_width, self.__ui_height)
        self.move(self.__ui_pos)

        # asset_path = os.path.dirname(__file__) + "/assets/asset.png"

        # Main Layout
        main_lyt = QVBoxLayout()
        main_lyt.setContentsMargins(7, 9, 7, 9)
        main_lyt.setSpacing(7)
        self.setLayout(main_lyt)

        self.__ui_character_lbl = QLabel("Name")
        self.__ui_character_lbl.setStyleSheet("QLabel{font-size:13px;font-weight:bold;}")
        main_lyt.addWidget(self.__ui_character_lbl, alignment=Qt.AlignCenter)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Raised)
        main_lyt.addWidget(line)

        btn_lyt = QVBoxLayout()
        main_lyt.addLayout(btn_lyt)

        options_lyt = QGridLayout()
        main_lyt.addLayout(options_lyt)

        self.__ui_uv_publish_cb = QCheckBox("Publish UV")
        self.__ui_uv_publish_cb.stateChanged.connect(self.__on_uv_publish_state_changed)
        options_lyt.addWidget(self.__ui_uv_publish_cb, 0, 0, 1, 2)
        self.__ui_look_publish_cb = QCheckBox("Publish Look")
        self.__ui_look_publish_cb.stateChanged.connect(self.__on_look_publish_state_changed)
        options_lyt.addWidget(self.__ui_look_publish_cb, 1, 0)
        self.__ui_look_name = QLineEdit()
        self.__ui_look_name.setPlaceholderText("Default Look")
        self.__ui_look_name.textChanged.connect(self.__on_look_name_changed)
        options_lyt.addWidget(self.__ui_look_name, 1, 1)

        self.__ui_publish_btn = QPushButton("Publish")
        self.__ui_publish_btn.clicked.connect(self.__on_publish)
        options_lyt.addWidget(self.__ui_publish_btn, 2, 0, 1, 2)

    def __refresh_ui(self):
        """
        Refresh the ui according to the model attribute
        :return:
        """
        self.__ui_look_publish_cb.setChecked(self.__publish_look)
        self.__ui_uv_publish_cb.setChecked(self.__publish_uv)
        self.__ui_look_name.setEnabled(self.__publish_look)
        self.__ui_character_lbl.setText(self.__asset_name)

        no_empty_sel = len(self.__selection) > 0
        self.__ui_publish_btn.setEnabled(no_empty_sel and (self.__publish_look or self.__publish_uv))

    def __on_uv_publish_state_changed(self, state):
        """
        On publish UV checkbox checked
        :param state
        :return:
        """
        self.__publish_uv = state == 2
        self.__refresh_ui()

    def __on_look_publish_state_changed(self, state):
        """
        On publish look checkbox checked
        :param state
        :return:
        """
        self.__publish_look = state == 2
        self.__refresh_ui()

    def __on_look_name_changed(self, value):
        """
        On Look name changed
        :param value
        :return:
        """
        self.__look_name = value

    def __on_selection_changed(self, *args, **kwargs):
        """
        On scene selection changed
        :param args
        :param kwargs
        :return:
        """
        self.__retrieve_datas()
        self.__refresh_ui()

    def __retrieve_datas(self):
        """
        Retrieve all the detas (selection, abc dir, abc name and texture nodes)
        :return:
        """
        self.__selection = pm.ls(selection=True)
        self.__retrieve_abc_dir_and_name()
        self.__texture_node.clear()
        if len(self.__selection) == 0: return
        shapes = pm.listRelatives(self.__selection, allDescendents=True, shapes=True)
        if len(shapes) == 0: return
        shading_nodes = pm.listConnections(shapes, type='shadingEngine')
        if len(shading_nodes) == 0: return
        file_nodes = pm.listHistory(shading_nodes, type="file")
        if len(file_nodes) == 0: return
        image_nodes = pm.listHistory(shading_nodes, type="aiImage")
        if len(image_nodes) == 0: return
        self.__texture_node = list(dict.fromkeys(file_nodes + image_nodes))

    def __replace_texture_node_to_tx(self):
        """
        Replace texture path by tx textures
        :return:
        """
        for tex_node in self.__texture_node:
            tex_path = CharacterPublisher.get_path_from_texture_node(tex_node)
            if tex_path is None: continue

            color_space = tex_node.colorSpace.get()
            render_color_space = "ACEScg"

            # Already TX
            if tex_path.endswith(".tx"): continue

            tx_path, tx_path_legacy = CharacterPublisher.texture_path_to_output_tx_path(
                tex_path, color_space, render_color_space)

            if os.path.isfile(tx_path):
                updated_path = tx_path
            elif os.path.isfile(tx_path_legacy):
                updated_path = tx_path_legacy
            else:
                # No TX found
                continue

            tex_node.ignoreColorSpaceFileRules.set(1)

            CharacterPublisher.set_path_to_texture_node(tex_node, updated_path)

            print(f"Replace {tex_path} -> {updated_path}")

    def __retrieve_abc_dir_and_name(self):
        """
        Retrieve ABC Dir and ABC Name
        :return:
        """
        if len(self.__selection) == 0:
            return

        self.__abc_dir = os.path.join(self.__asset_dir, "abc")
        higher_version_file = 0
        if os.path.exists(self.__abc_dir):
            for file in os.listdir(self.__abc_dir):
                if not os.path.isfile(self.__abc_dir + "/" + file):
                    continue
                match = re.search(r".*v([0-9]+).abc", file)
                if not match:
                    continue
                version = int(match.group(1))
                if version > higher_version_file:
                    higher_version_file = version

        num = higher_version_file + 1
        num_str = str(num)
        self.__abc_name = self.__asset_name + "_mod.v" + (3 - len(num_str)) * '0' + num_str + ".abc"
        while os.path.exists(self.__abc_dir + "/" + self.__abc_name):
            num_str = str(num)
            num_str = (3 - len(num_str)) * '0' + num_str
            self.__abc_name = self.__asset_name + "_mod.v" + num_str + ".abc"
            num += 1

    def abc_export(self):
        """
        Export UV
        :return:
        """
        abc_path = os.path.join(self.__abc_dir, self.__abc_name)
        abc_path = abc_path.replace("\\", "/")
        os.makedirs(self.__abc_dir, exist_ok=True)
        geo_list_to_export = [s.longName() for s in self.__selection]
        geo_string_to_export = " -root ".join(geo_list_to_export)
        job = '-frameRange 1 1 -stripNamespaces -uvWrite -writeColorSets -worldSpace -writeFaceSets -dataFormat ogawa -root %s -file "%s"' % (
            geo_string_to_export, abc_path)
        pm.AbcExport(j=job)

        standin = pm.createNode("aiStandIn", n=self.__abc_name.split(".")[0] + "Shape")
        parent = standin.getParent()
        pm.rename(parent, self.__abc_name.split(".")[0])
        standin.dso.set(abc_path)
        return standin

    def __build_shader_operator(self, standin, sel):
        """
        Build shader for look
        :param standin
        :param sel
        :return:
        """
        # Get the selected objects
        ai_merge = pm.createNode("aiMerge", n="aiMerge_%s" % standin.getParent().name())
        empty_displace = None
        shaders_used = []
        pm.addAttr(ai_merge, ln="mtoa_constant_is_target", attributeType="bool", defaultValue=True)
        pm.connectAttr(ai_merge + ".out", standin + ".operators[0]")
        meshes = pm.listRelatives(sel, allDescendents=True, shapes=True)
        for m in meshes:
            if "ShapeOrig" in m.name():
                meshes.remove(m)

        counter = 0
        for m in meshes:
            selection = m
            namespace = selection.namespace()
            selection = selection.longName()
            selection = selection.replace(namespace, "")
            selection = selection.replace("|", "/")
            # selection = selection + "*"

            sgs = m.outputs(type='shadingEngine')
            sgs = list(set(sgs))
            set_shader = pm.createNode("aiSetParameter", n="setShader_" + m)
            selection_attr = set_shader.attr("selection")
            selection_attr.set(selection)
            pm.connectAttr(set_shader + ".out", ai_merge + ".inputs[%s]" % (counter), f=True)
            counter += 1

            shader = ""
            displacement_shader_string = ""
            all_disp = None
            shader_maya_disp = None
            auto_bump = False
            if len(sgs) == 1:
                sg = sgs[0]
                if sg.aiSurfaceShader.isConnected():
                    shader_maya = sg.aiSurfaceShader.inputs()[0]
                    shader += "'%s'" % shader_maya
                    shaders_used.append(shader_maya)
                elif sg.surfaceShader.isConnected():
                    shader_maya = sg.surfaceShader.inputs()[0]
                    shader += "'%s'" % shader_maya
                    shaders_used.append(shader_maya)

                if sg.displacementShader.isConnected():
                    shader_maya_disp = sg.displacementShader.inputs()[0]
                    displacement_shader_string = "'%s'" % shader_maya_disp
                    shaders_used.append(shader_maya_disp)
            else:
                all_disp = [sg.displacementShader for sg in sgs if sg.displacementShader.isConnected()]
                for sg in sgs:
                    if sg.aiSurfaceShader.isConnected():
                        shader_maya = sg.aiSurfaceShader.inputs()[0]
                        shaders_used.append(shader_maya)
                        shader += "'%s' " % shader_maya
                    elif sg.surfaceShader.isConnected():
                        shader_maya = sg.surfaceShader.inputs()[0]
                        shaders_used.append(shader_maya)
                        shader += "'%s' " % (sg.surfaceShader.inputs()[0])
                    # Check if there is any displacement shader because if there is one, all sg will need a displacement
                    # So if an object has two shaders one with a displace and one without, we will need to create an empty shaders
                    # to make the operator per face assignement work
                    if len(all_disp) > 0:
                        if sg.displacementShader.isConnected():
                            shader_maya = sg.displacementShader.inputs()[0]
                            shaders_used.append(shader_maya)
                            displacement_shader_string += "'%s' " % (sg.displacementShader.inputs()[0])
                        else:
                            if not empty_displace:
                                empty_displace = pm.shadingNode("displacementShader", asShader=True)
                            autobump_attr = empty_displace.attr("aiDisplacementAutoBump")
                            autobump_attr.set(0)
                            pm.connectAttr(empty_displace.displacement, sg.displacementShader)
                            shaders_used.append(empty_displace)
                            displacement_shader_string += "'%s' " % (empty_displace)

            pm.setAttr(set_shader + ".assignment[0]", "shader=%s" % (shader), type="string")
            if displacement_shader_string != "":
                pm.setAttr(set_shader + ".assignment[1]", "disp_map=%s" % (displacement_shader_string), type="string")
                if all_disp:
                    all_disp[0].inputs()[0].aiDisplacementAutoBump.get()

                else:
                    if shader_maya_disp.aiDisplacementAutoBump.get() == True:
                        auto_bump = True
                if auto_bump:
                    pm.setAttr(set_shader + ".assignment[2]", "bool disp_autobump=True", type="string")

            # CATCLARK
            sss_set_name = m.ai_sss_setname.get()
            ai_disp_height = m.aiDispHeight.get()
            casts_shadows = m.castsShadows.get()
            cat_clark_type = m.aiSubdivType.get()
            cat_clark_subdiv = m.aiSubdivIterations.get()
            traceSets= m.aiTraceSets.get()
            if cat_clark_type > 0 and cat_clark_subdiv > 0:
                pm.setAttr(set_shader + ".assignment[3]", "subdiv_type='catclark'", type="string")
                pm.setAttr(set_shader + ".assignment[4]", "subdiv_iterations=%s" % (cat_clark_subdiv), type="string")
            if sss_set_name != "":
                pm.setAttr(set_shader + ".assignment[5]", "string ai_sss_setname=\"%s\"" % (sss_set_name),
                           type="string")
            if casts_shadows == 0:
                pm.setAttr(set_shader + ".assignment[6]", "visibility=253", type="string")
            if ai_disp_height != 1:
                pm.setAttr(set_shader + ".assignment[7]", "disp_height=%s" % (ai_disp_height), type="string")
            if traceSets:
                pm.setAttr(set_shader+".assignment[8]","trace_sets='%s'"%(traceSets), type="string")
        return shaders_used

    def __export_arnold_graph(self, standin, shaders_used):
        """
        Export look
        :param standin
        :param shaders_used
        :return:
        """
        look_dir = os.path.join(self.__asset_dir, "publish")
        # Check if default look or special one
        if len(self.__look_name) > 0:
            look_dir = os.path.join(look_dir, "look", self.__look_name)
        os.makedirs(look_dir, exist_ok=True)
        if len(self.__look_name) > 0:
            path = os.path.join(look_dir, self.__asset_name + "_"+ self.__look_name +"_operator.")
        else:
            path = os.path.join(look_dir, self.__asset_name + "_operator.")
        higher_version_file = 0
        for file in os.listdir(look_dir):
            if os.path.isfile(look_dir + "/" + file):
                match = re.search(r".*v([0-9]+).ass", file)
                if match:
                    version = int(match.group(1))
                    if version > higher_version_file:
                        higher_version_file = version
        num = higher_version_file + 1
        num_str = str(num)
        path_test = path + "v" + (3 - len(num_str)) * '0' + num_str + ".ass"

        while os.path.exists(path_test):
            num += 1
            num_str = str(num)
            num_str = (3 - len(num_str)) * '0' + num_str
            path_test = path + "v" + num_str + ".ass"

        path = path_test
        look = pm.listConnections(standin + ".operators")
        export_list = look + shaders_used
        pm.other.arnoldExportAss(export_list, f=path, s=True, asciiAss=True, mask=6160, lightLinks=0, shadowLinks=0,
                                 fullPath=0)

    def __on_publish(self):
        """
        On submit publish
        :return:
        """
        CharacterPublisher.__check_color_sets("Pref")
        self.__replace_texture_node_to_tx()
        sel = self.__selection
        if self.__publish_uv:
            standin = self.abc_export()
        else:
            standin = pm.createNode("aiStandIn", n="tmp_standin")

        if self.__publish_look:
            shaders_used = self.__build_shader_operator(standin, sel)
            self.__export_arnold_graph(standin, shaders_used)

        # if not self.__publish_uv:
        #     pm.delete(standin.getTransform())
