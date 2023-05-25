from abc import ABCMeta, abstractmethod
import nuke
from common.utils import *
from .RuleSet import Variable
from .LayoutManager import LayoutManager
from .UnpackMode import BACKDROP_LAYER, BACKDROP_MERGE

# ######################################################################################################################

_SHUFFLE_LAYER_KEY = "shuffle_layer"
_SHUFFLE_COLOR_KEY = "color"
_BACKDROP_SHUFFLE = "SHUFFLE"
_PREFIX_SHUFFLE = "shuffle_"
_PREFIX_MERGE_SHUFFLE = "merge_shuffle_"
_PREFIX_MERGE_SHUFFLED = "shuffled_"
_PREFIX_DOT = "dot_"
_DISTANCE_COLUMN_SHUFFLE = 2
_DISTANCE_READ_TO_SHUFFLE = 1.7
_HEIGHT_COLUMN_SHUFFLE = 3
_DISTANCE_OUTPUT_SHUFFLE = 1.7

# ######################################################################################################################


class ShuffleMode:
    __metaclass__ = ABCMeta

    def __init__(self, layout_manager, shuffle_data = None):
        self._layout_manager = layout_manager
        self._var_set = None
        self.__shuffle_layer_option = shuffle_data[_SHUFFLE_LAYER_KEY] if shuffle_data is not None else None
        self.__shuffle_color_option = shuffle_data[_SHUFFLE_COLOR_KEY] \
            if _SHUFFLE_COLOR_KEY in shuffle_data else None
        self._shuffle_nodes = {}
        self._output_nodes = {}

    def set_var_set(self, var_set):
        self._var_set = var_set

    def run(self):
        if self._var_set is None:
            return
        self.__shuffle_vars()
        self.__merge_shuffle()
        self.__output_shuffle()

    def __merge_shuffle(self):
        if len(self._shuffle_nodes) > 0:
            half_height_col = _HEIGHT_COLUMN_SHUFFLE * 3/4.0
            for var_name, var_shuffle_nodes in self._shuffle_nodes.items():
                shuffle_backdrop_longname = ".".join([BACKDROP_LAYER, var_name, _BACKDROP_SHUFFLE])
                first_shuffle_node = var_shuffle_nodes[0]
                dot_node = nuke.nodes.Dot(name=_PREFIX_DOT + var_name, inputs=[first_shuffle_node])
                self._layout_manager.add_nodes_to_backdrop(shuffle_backdrop_longname, [dot_node])
                self._layout_manager.add_node_layout_relation(first_shuffle_node, dot_node,
                                                              LayoutManager.POS_BOTTOM, half_height_col)
                current_node = dot_node
                for node in var_shuffle_nodes[1:]:
                    merge_node = nuke.nodes.Merge(name=_PREFIX_MERGE_SHUFFLE + var_name, operation="plus",
                                                  A="rgb", inputs=[current_node, node])
                    self._layout_manager.add_nodes_to_backdrop(shuffle_backdrop_longname, [merge_node])
                    self._layout_manager.add_node_layout_relation(node, merge_node, LayoutManager.POS_BOTTOM,
                                                                  half_height_col)
                    current_node = merge_node

                current_node["name"].setValue(_PREFIX_MERGE_SHUFFLED + var_name)
                self._output_nodes[var_name] = (current_node, len(var_shuffle_nodes))

    def __shuffle_channel(self, input_node, name_var, channel, shuffle_backdrop_longname):
        shuffle_node = nuke.createNode("Shuffle2")
        shuffle_node["in1"].setValue(channel)
        shuffle_node["postage_stamp"].setValue(True)
        shuffle_node.setName(_PREFIX_SHUFFLE + name_var + "_"+ channel.replace("RGBA_",""))
        shuffle_node.setInput(0, input_node)
        self._layout_manager.add_nodes_to_backdrop(shuffle_backdrop_longname,[shuffle_node])
        self._layout_manager.add_node_layout_relation(input_node, shuffle_node, LayoutManager.POS_BOTTOM,
                                                      _HEIGHT_COLUMN_SHUFFLE/4.0)
        self._shuffle_nodes[name_var].append(shuffle_node)

    def __shuffle_light_group(self, var):
        name_var = var.get_name()
        node_var = var.get_node()
        if self.__shuffle_layer_option is not None and name_var not in self.__shuffle_layer_option:
            self._var_set.active_var(var, False)
            self._output_nodes[name_var] = (node_var, 0)
            return False
        backdrop_longname = ".".join([BACKDROP_LAYER, name_var])
        shuffle_backdrop_longname = ".".join([backdrop_longname, _BACKDROP_SHUFFLE])
        init_dot = nuke.nodes.Dot(name=_PREFIX_DOT + name_var, inputs=[node_var])
        self._layout_manager.add_nodes_to_backdrop(backdrop_longname, [init_dot])
        if self.__shuffle_color_option is not None:
            self._layout_manager.add_backdrop_option(shuffle_backdrop_longname, "color", self.__shuffle_color_option)
        self._layout_manager.add_backdrop_option(shuffle_backdrop_longname, "margin_bottom", 56)
        self._layout_manager.add_backdrop_option(shuffle_backdrop_longname, "font_size", 30)
        self._layout_manager.add_node_layout_relation(node_var, init_dot, LayoutManager.POS_RIGHT,
                                                      _DISTANCE_READ_TO_SHUFFLE / 2.0)
        dot_node = nuke.nodes.Dot(name=_PREFIX_DOT + name_var, inputs=[init_dot])
        self._layout_manager.add_nodes_to_backdrop(backdrop_longname, [dot_node])
        self._layout_manager.add_node_layout_relation(init_dot, dot_node, LayoutManager.POS_TOP,
                                                      _HEIGHT_COLUMN_SHUFFLE)

        detailed_channels = node_var.channels()
        processed_channels = []
        lg_channels = []
        for channel in detailed_channels:
            channel_split = channel.split(".")[0]
            if channel_split.startswith("RGBA_") and channel_split not in processed_channels:
                prev_node = dot_node
                dot_node = nuke.nodes.Dot(name=_PREFIX_DOT + name_var, inputs=[prev_node])

                if len(lg_channels) == 0:
                    dist = _DISTANCE_READ_TO_SHUFFLE / 2.0
                else:
                    dist = _DISTANCE_COLUMN_SHUFFLE
                self._layout_manager.add_nodes_to_backdrop(shuffle_backdrop_longname, [dot_node])

                self._layout_manager.add_node_layout_relation(prev_node, dot_node, LayoutManager.POS_RIGHT,
                                                              dist)
                lg_channels.append((channel_split, dot_node))
                processed_channels.append(channel_split)

        if len(lg_channels) > 0:
            self._shuffle_nodes[name_var] = []
            for lg_channel, node in lg_channels:
                self.__shuffle_channel(node, name_var, lg_channel, shuffle_backdrop_longname)
            self._var_set.active_var(var, False)

    def __shuffle_vars(self):
        for var in self._var_set.get_active_vars()[:]:
            self.__shuffle_light_group(var)

    def __output_shuffle(self):
        max_len = 0
        for output_node, len_shuffle in self._output_nodes.values():
            if len_shuffle > max_len : max_len = len_shuffle

        for var_name, output_node_data in self._output_nodes.items():
            output_node, len_shuffle = output_node_data
            diff_len = max_len - len_shuffle
            if max_len == 0:
                dist = _DISTANCE_OUTPUT_SHUFFLE
            else:
                if len_shuffle != 0:
                    dist = diff_len*_DISTANCE_COLUMN_SHUFFLE + _DISTANCE_OUTPUT_SHUFFLE
                else:
                    dist = (max_len-1)*_DISTANCE_COLUMN_SHUFFLE + _DISTANCE_READ_TO_SHUFFLE + _DISTANCE_OUTPUT_SHUFFLE
            dot_node = nuke.nodes.Dot(name=_PREFIX_DOT+var_name, inputs=[output_node])
            self._layout_manager.add_nodes_to_backdrop(BACKDROP_MERGE, [dot_node])
            self._layout_manager.add_node_layout_relation(output_node, dot_node,
                                                          LayoutManager.POS_RIGHT, dist)
            self._var_set.active_var(Variable(var_name, dot_node))