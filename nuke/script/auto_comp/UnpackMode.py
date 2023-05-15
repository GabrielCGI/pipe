import os
import re
import nuke
import nukescripts
from common.utils import *
from .LayoutManager import LayoutManager

# ######################################################################################################################

_PREFIX_POSTAGE = "postage_"
_BACKDROP_INPUTS = "INPUTS"
_BACKDROP_LAYER_INPUTS = "READ"
_BACKDROP_INPUTS_COLOR = (194, 100, 120)
_BACKDROP_LAYER_READ_COLOR = (115, 150, 190)
_DEFAULT_LAYER_COLOR = (40,90,150)

# ######################################################################################################################

class UnpackMode:

    @staticmethod
    def __get_last_seq_from_layer(layer_path):
        for seq_name in reversed(os.listdir(layer_path)):
            seq_dir_path = os.path.join(layer_path, seq_name)
            if os.path.isdir(seq_dir_path):
                start_frame = None
                end_frame = None
                utility_path = None
                seq_path = None
                for frame in os.listdir(seq_dir_path):
                    match = re.match(r"^"+seq_name+r"(_utility)?\.([0-9]{4})\.exr$", frame)
                    if match:
                        if match.group(1) is not None:
                            frame_count = int(match.group(2))
                            if frame_count < start_frame or start_frame is None:
                                start_frame = frame_count
                            if frame_count > end_frame or end_frame is None:
                                end_frame = frame_count
                            seq_path = os.path.join(seq_dir_path,seq_name+".####.exr").replace("\\","/")
                        else:
                            utility_path = os.path.join(seq_dir_path,seq_name+"_utility.####.exr").replace("\\","/")
                if seq_path is not None:
                    return seq_path, utility_path, start_frame, end_frame
        return None

    @staticmethod
    def __create_read_with_postage(name, seq_path, start_frame, end_frame):
        read_node = nuke.nodes.Read(name=name, file=seq_path, first=start_frame, last=end_frame)
        # read_node = nuke.createNode("Read") #TODO remove
        # read_node["name"].setValue(name)
        # read_node["file"].setValue(seq_path)
        # read_node["first"].setValue(start_frame)
        # read_node["last"].setValue(end_frame)
        postage_stamp = nuke.nodes.PostageStamp(name=_PREFIX_POSTAGE+name, hide_input=True, inputs=[read_node], postage_stamp=True)
        # postage_stamp = nuke.createNode("PostageStamp") #TODO remove
        # postage_stamp["name"].setValue(_PREFIX_POSTAGE+name)
        # postage_stamp["hide_input"].setValue(True)
        # postage_stamp.setInput(0,read_node)
        # postage_stamp["postage_stamp"].setValue(True)
        return read_node, postage_stamp

    def __init__(self, name, var_set, shuffle_mode, merge_mode, layout_manager):
        self.__name = name
        self.__var_set = var_set
        self.__layout_manager = layout_manager
        self.__shuffle_mode = shuffle_mode
        self.__merge_mode = merge_mode
        self.__shuffle_mode.set_var_set(self.__var_set)
        self.__merge_mode.set_var_set(self.__var_set)

    def get_name(self):
        return self.__name

    def get_var_set(self):
        return self.__var_set

    def get_shuffle_mode(self):
        return self.__shuffle_mode

    def get_merge_mode(self):
        return self.__merge_mode

    def is_valid(self):
        return self.__shuffle_mode is not None and self.__merge_mode is not None
    
    # Retrieve the layers in the shot corresponding to the variable in ruleset
    def __scan_layers(self, shot_path):
        render_path = os.path.join(shot_path, "render_out")
        render_path, os.path.isdir(render_path)
        for render_layer in os.listdir(render_path):
            layer_path = os.path.join(render_path, render_layer)
            if not os.path.isdir(layer_path):
                continue
            # Get the last sequence for the layer
            seq_data = UnpackMode.__get_last_seq_from_layer(layer_path)
            if seq_data is None:
                continue
            seq_path, utility_path, start_frame, end_frame = seq_data

            # Verify that the layer is in the variable
            start_var = self.__var_set.get_start_variable_valid_for(render_layer)
            if start_var is None:
                continue

            name = start_var.get_name()
            read_node, postage_stamp = UnpackMode.__create_read_with_postage(name,seq_path,start_frame,end_frame)
            to_inputs_backdrop = [read_node]
            to_layer_inputs_backdrop = [postage_stamp]
            if utility_path is not None:
                utility_read_node, utility_postage_stamp = \
                    UnpackMode.__create_read_with_postage("utility_"+name,utility_path,start_frame,end_frame)
                merge_node = nuke.nodes.Merge(operation="over", also_merge="all", inputs=[utility_postage_stamp, postage_stamp])
                # merge_node = nuke.createNode("Merge") #TODO remove
                # merge_node["operation"].setValue("over")
                # merge_node["also_merge"].setValue("all")
                # merge_node.setInput(1, utility_postage_stamp)
                # merge_node.setInput(0, postage_stamp)
                to_inputs_backdrop.append(utility_read_node)
                to_layer_inputs_backdrop.append(utility_postage_stamp)
                to_layer_inputs_backdrop.append(merge_node)
                start_var.set_node(merge_node)
                self.__layout_manager.add_node_layout_relation(read_node, utility_read_node)
                self.__layout_manager.add_node_layout_relation(postage_stamp, merge_node)
                self.__layout_manager.add_node_layout_relation(merge_node, utility_postage_stamp, LayoutManager.POS_TOP)
            else:
                start_var.set_node(postage_stamp)

            input_layer_bd_longname = ".".join([_BACKDROP_INPUTS,render_layer])
            layer_read_bd_longname = ".".join([render_layer,_BACKDROP_LAYER_INPUTS])
            color = start_var.get_option("color")
            if color is None : color = _DEFAULT_LAYER_COLOR

            # INPUTS
            self.__layout_manager.add_backdrop_option(_BACKDROP_INPUTS, "color", _BACKDROP_INPUTS_COLOR)
            # INPUTS.LAYER
            self.__layout_manager.add_nodes_to_backdrop(input_layer_bd_longname,to_inputs_backdrop)
            # self.__layout_manager.add_backdrop_option(input_layer_bd_longname,"font_size",20)
            self.__layout_manager.add_backdrop_option(input_layer_bd_longname,"color", color)
            # LAYER
            self.__layout_manager.add_backdrop_option(render_layer,"color", color)
            # LAYER.READ
            self.__layout_manager.add_nodes_to_backdrop(layer_read_bd_longname,to_layer_inputs_backdrop)
            # self.__layout_manager.add_backdrop_option(layer_read_bd_longname,"font_size",20)
            self.__layout_manager.add_backdrop_option(layer_read_bd_longname,"color", _BACKDROP_LAYER_READ_COLOR)

            # self.__layout_manager.add_backdrop_layout_relation(_BACKDROP_INPUTS, render_layer, LayoutManager.POS_TOP)

            # Add the start_var to the active variable (for the merge part)
            self.__var_set.active_var(start_var)


    def unpack(self, shot_path):
        # Retrieve Layers and create Start Var (Read nodes)
        self.__scan_layers(shot_path)
        # Shuffle those layers if needed
        # self.__shuffle_mode.run()
        # Merge all the nodes with right rules
        self.__merge_mode.run()
        # Organize all the nodes
        self.__layout_manager.build_layout_node_graph()
        # Organize all the backdrops
        self.__layout_manager.build_layout_backdrops()
