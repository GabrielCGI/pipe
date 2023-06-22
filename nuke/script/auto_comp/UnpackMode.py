import os
import re
import nuke
import nukescripts
from common.utils import *
from .LayoutManager import LayoutManager
from .RuleSet import StartVariable

# ######################################################################################################################

_PREFIX_POSTAGE = "postage_"
_PREFIX_UTILITY = "utility_"
_PREFIX_UTILITY_MERGE = "utility_merge_"
_BACKDROP_INPUTS = "INPUTS"
BACKDROP_LAYER = "LAYER"
BACKDROP_MERGE = "MERGE"
_BACKDROP_LAYER_READS = "READ"
BACKDROP_LAYER_SHUFFLE = "SHUFFLE"

_BACKDROP_LAYER_READS_FONT_SIZE = 30
_BACKDROP_INPUTS_COLOR = (120, 120, 120)
DEFAULT_LAYER_COLOR = (40, 90, 150)
_INPUTS_LAYER_DISTANCE = 1.5
_LAYER_READ_DISTANCE = 1.8
_LAYER_POSTAGE_DISTANCE = 6


# ######################################################################################################################

class UnpackMode:

    # Get a lightened version of the input color
    @staticmethod
    def __ligthen_color(r, g, b):
        ligthen_ratio = 0.3
        return int(r + (255 - r) * ligthen_ratio), int(g + (255 - g) * ligthen_ratio), \
               int(b + (255 - b) * ligthen_ratio)

    # Get a darkened version of the input color
    @staticmethod
    def __darken_color(r, g, b):
        darken_ratio = 0.3

        return int(r * (1-darken_ratio)), int(g *(1-darken_ratio)), int(b *(1-darken_ratio))

    # Get the last sequence and utility sequence of a layer
    @staticmethod
    def get_last_seq_from_layer(layer_path):
        if not os.path.isdir(layer_path):
            return None
        for seq_name in reversed(os.listdir(layer_path)):
            seq_dir_path = os.path.join(layer_path, seq_name)
            if os.path.isdir(seq_dir_path):
                start_frame = None
                end_frame = None
                utility_path = None
                seq_path = None
                for frame in os.listdir(seq_dir_path):
                    match = re.match(r"^" + seq_name + r"(_utility)?\.([0-9]{4})\.exr$", frame)
                    if match:
                        if match.group(1) is not None:
                            frame_count = int(match.group(2))
                            if frame_count < start_frame or start_frame is None:
                                start_frame = frame_count
                            if frame_count > end_frame or end_frame is None:
                                end_frame = frame_count
                            seq_path = os.path.join(seq_dir_path, seq_name + ".####.exr").replace("\\", "/")
                        else:
                            utility_path = os.path.join(seq_dir_path, seq_name + "_utility.####.exr").replace("\\", "/")
                if seq_path is not None:
                    return seq_path, utility_path, start_frame, end_frame
        return None

    # Create a read node with a postage stamp node
    @staticmethod
    def __create_read_with_postage(name, seq_path, start_frame, end_frame):
        read_node = nuke.nodes.Read(name=name, file=seq_path, first=start_frame, last=end_frame)
        postage_stamp = nuke.nodes.PostageStamp(name=_PREFIX_POSTAGE + name, hide_input=True, inputs=[read_node],
                                                postage_stamp=True)
        return read_node, postage_stamp

    def __init__(self, config_path, name, var_set, shuffle_mode, merge_mode, layout_manager):
        self.__name = name
        self.__config_path = config_path
        self.__var_set = var_set
        self.__start_vars_to_unpack = []
        self.__layout_manager = layout_manager
        self.__shuffle_mode = shuffle_mode
        self.__merge_mode = merge_mode
        self.__shuffle_mode.set_var_set(self.__var_set)
        self.__merge_mode.set_var_set(self.__var_set)

    # Getter if the Unpack mode name
    def get_name(self):
        return self.__name

    # Getter if the Unpack mode config path
    def get_config_path(self):
        return self.__config_path

    # Getter if the Unpack mode variable set
    def get_var_set(self):
        return self.__var_set

    # Getter if the Unpack mode Shuffle mode
    def get_shuffle_mode(self):
        return self.__shuffle_mode

    # Getter if the Unpack mode Merge Mode
    def get_merge_mode(self):
        return self.__merge_mode

    # Getter of whether the Unpack Mode is valid or not (Shuffle and Merge not None)
    def is_valid(self):
        return self.__shuffle_mode is not None and self.__merge_mode is not None

    # Retrieve the layers in the shot corresponding to the variable in ruleset
    def scan_layers(self, shot_path, layer_filter_arr =None):
        if not os.path.isdir(shot_path):
            return
        if shot_path.endswith("render_out"):
            render_path = shot_path
        else:
            render_path = os.path.join(shot_path, "render_out")
        if not os.path.isdir(render_path):
            return
        self.__start_vars_to_unpack = []
        layer_type_taken = []
        for render_layer in os.listdir(render_path):
            if layer_filter_arr is not None and render_layer not in layer_filter_arr: continue
            # Verify that the layer is in the variable
            start_var = self.__var_set.get_start_variable_valid_for(render_layer)
            if start_var is None: continue
            layer_type = start_var.get_name()
            if layer_type in layer_type_taken:
                start_var = StartVariable.copy(start_var)
            else:
                layer_type_taken.append(layer_type)
            start_var.set_layer(render_layer)
            self.__start_vars_to_unpack.append(start_var)
        self.__start_vars_to_unpack.sort(key=lambda x: x.get_order())

    # Getter of whether the layer is scanned or not
    def is_layer_scanned(self, layer):
        for start_var in self.__start_vars_to_unpack:
            # if start_var.is_rule_valid(layer):
            if start_var.get_layer() == layer:
                return start_var
        return False

    # Getter of whether the layer is scanned or not
    def is_layer_name_scanned(self, layer_name):
        for start_var in self.__start_vars_to_unpack:
            if start_var.get_name() == layer_name:
                return True
        return False

    # Retrieve the layers, create the read node, postages and setup layout options
    def __unpack_layers(self, shot_path):
        render_path = os.path.join(shot_path, "render_out")
        read_nodes = []
        postage_nodes = []
        # for each layer
        for start_var in self.__start_vars_to_unpack:
            render_layer = start_var.get_layer()
            layer_path = os.path.join(render_path, render_layer)
            if not os.path.isdir(layer_path):
                continue
            # Get the last sequence for the layer
            seq_data = UnpackMode.get_last_seq_from_layer(layer_path)
            if seq_data is None:
                continue
            seq_path, utility_path, start_frame, end_frame = seq_data

            name = start_var.get_name()
            read_node, postage_stamp = UnpackMode.__create_read_with_postage(render_layer, seq_path, start_frame, end_frame)
            postage_nodes.append(postage_stamp)
            to_inputs_backdrop = [read_node]
            to_layer_inputs_backdrop = [postage_stamp]
            # If Utility exists compute it and connect it
            if utility_path is not None:
                utility_read_node, utility_postage_stamp = \
                    UnpackMode.__create_read_with_postage(_PREFIX_UTILITY + render_layer, utility_path, start_frame, end_frame)
                merge_node = nuke.nodes.Merge(operation="over", also_merge="all",
                                              inputs=[utility_postage_stamp, postage_stamp])
                merge_node.setName(_PREFIX_UTILITY_MERGE + render_layer)
                read_nodes.append((read_node, utility_read_node))

                to_inputs_backdrop.append(utility_read_node)
                to_layer_inputs_backdrop.append(utility_postage_stamp)
                to_layer_inputs_backdrop.append(merge_node)
                start_var.set_node(merge_node)
                self.__layout_manager.add_node_layout_relation(read_node, utility_read_node)
                self.__layout_manager.add_node_layout_relation(postage_stamp, merge_node, mult_distance=1.3)
                self.__layout_manager.add_node_layout_relation(merge_node, utility_postage_stamp, LayoutManager.POS_TOP)
            else:
                read_nodes.append((read_node))
                start_var.set_node(postage_stamp)

            # Get the Backdrops name
            input_layer_bd_longname = ".".join([_BACKDROP_INPUTS, render_layer])
            layer_bd_longname = ".".join([BACKDROP_LAYER, render_layer])
            layer_read_bd_longname = ".".join([layer_bd_longname, _BACKDROP_LAYER_READS])
            layer_shuffle_bd_longname = ".".join([layer_bd_longname, BACKDROP_LAYER_SHUFFLE])
            color = start_var.get_option("color")
            if color is None: color = DEFAULT_LAYER_COLOR

            # Generate BackDrops options (color, font_size)

            # INPUTS.LAYER
            self.__layout_manager.add_nodes_to_backdrop(input_layer_bd_longname, to_inputs_backdrop)
            self.__layout_manager.add_backdrop_option(input_layer_bd_longname, "font_size",
                                                      _BACKDROP_LAYER_READS_FONT_SIZE)
            self.__layout_manager.add_backdrop_option(input_layer_bd_longname, "color", color)
            # LAYERS.LAYER_instance
            self.__layout_manager.add_backdrop_option(layer_bd_longname, "color", color)
            # LAYERS.LAYER_instance.READ
            self.__layout_manager.add_nodes_to_backdrop(layer_read_bd_longname, to_layer_inputs_backdrop)
            self.__layout_manager.add_backdrop_option(layer_read_bd_longname, "font_size",
                                                      _BACKDROP_LAYER_READS_FONT_SIZE)
            self.__layout_manager.add_backdrop_option(layer_read_bd_longname, "color",
                                                      UnpackMode.__darken_color(*color))

            self.__layout_manager.add_top_level_backdrop_layout_relation(BACKDROP_LAYER, _BACKDROP_INPUTS,
                                                                         LayoutManager.POS_TOP,
                                                                         LayoutManager.ALIGN_START,
                                                                         _INPUTS_LAYER_DISTANCE)

            # LAYERS.LAYER_instance.SHUFFLE
            self.__layout_manager.add_backdrop_option(layer_shuffle_bd_longname, "color",
                                                      UnpackMode.__ligthen_color(*color))

            # Add the start_var to the active variable (for the merge part)
            self.__var_set.active_var(start_var)

        # INPUTS
        self.__layout_manager.add_backdrop_option(_BACKDROP_INPUTS, "color", _BACKDROP_INPUTS_COLOR)

        # Add layout relations
        last = None
        for read_node in read_nodes:
            read = read_node[0]
            if last is not None:
                self.__layout_manager.add_node_layout_relation(last, read, LayoutManager.POS_RIGHT,
                                                               _LAYER_READ_DISTANCE)
            if len(read_node) == 2:
                last = read_node[1]
            else:
                last = read

        curr = postage_nodes[0]
        for postage_node in postage_nodes[1:]:
            self.__layout_manager.add_node_layout_relation(curr, postage_node, LayoutManager.POS_BOTTOM,
                                                           _LAYER_POSTAGE_DISTANCE)
            curr = postage_node

    # Run the AutoCOmp by unpacking layers, shuffling them, merging the outputs and building all the layouts
    def unpack(self, shot_path):
        if len(self.__start_vars_to_unpack) == 0: return
        # Retrieve the bounding box of the current graph to place correctly incoming graph
        self.__layout_manager.compute_current_bbox_graph()
        # Retrieve Layers and create Start Var (Read nodes)
        self.__unpack_layers(shot_path)
        # Shuffle those layers if needed
        self.__shuffle_mode.run()
        # Merge all the nodes with right rules
        self.__merge_mode.run()
        # Organize all the nodes
        self.__layout_manager.build_layout_node_graph()
        # Organize all the backdrops
        self.__layout_manager.build_layout_backdrops()
