from abc import ABCMeta, abstractmethod
import nuke
from common.utils import *
from .RuleSet import Variable
from .LayoutManager import LayoutManager
from .UnpackMode import BACKDROP_LAYER

# ######################################################################################################################

_BACKDROP_SHUFFLE = "SHUFFLE"
_PREFIX_SHUFFLE = "shuffle_"
_PREFIX_HANDLE = "handle_"

# ######################################################################################################################

class ShuffleMode:
    __metaclass__ = ABCMeta

    def __init__(self, shuffle_layer_option, layout_manager):
        self.__layout_manager = layout_manager
        self._var_set = None
        self.__shuffle_layer_option = shuffle_layer_option
        self._shuffle_nodes = {}

    def set_var_set(self, var_set):
        self._var_set = var_set

    @abstractmethod
    def run(self):
        pass

    def __shuffle_channel(self, input_node, name_var, channel):
        shuffle_node = nuke.createNode("Shuffle2")
        shuffle_node["in1"].setValue(channel)
        shuffle_node.setName(_PREFIX_SHUFFLE + name_var + "_"+ channel.replace("RGBA_",""))
        shuffle_node.setInput(0, input_node)
        self._shuffle_nodes[name_var].append(shuffle_node)

    def _shuffle_light_group(self):
        to_deactivate = []
        for var in self._var_set.get_active_vars():
            name_var = var.get_name()
            if name_var not in self.__shuffle_layer_option:
                continue
            node_var = var.get_node()
            shuffle_backdrop_longname = ".".join([BACKDROP_LAYER, name_var, _BACKDROP_SHUFFLE])
            dot = nuke.nodes.Dot(name=_PREFIX_HANDLE+name_var, inputs=[node_var])
            self.__layout_manager.add_nodes_to_backdrop(shuffle_backdrop_longname,[dot])
            self.__layout_manager.add_node_layout_relation(node_var, dot, LayoutManager.POS_RIGHT,3)
            dot_node_var = nuke.nodes.Dot(name=_PREFIX_HANDLE+name_var, inputs=[dot])
            self.__layout_manager.add_nodes_to_backdrop(shuffle_backdrop_longname,[dot_node_var])
            self.__layout_manager.add_node_layout_relation(dot, dot_node_var, LayoutManager.POS_TOP,3)

            detailed_channels = node_var.channels()
            lg_channels = []
            for channel in detailed_channels:
                channel_split = channel.split(".")[0]
                if channel_split.startswith("RGBA_") and channel_split not in lg_channels:
                    lg_channels.append(channel_split)
            if len(lg_channels) > 0:
                self._shuffle_nodes[name_var] = []
                for lg_channel in lg_channels:
                    self.__shuffle_channel(dot_node_var, name_var, lg_channel)
                to_deactivate.append(var)
        for var in to_deactivate:
            self._var_set.active_var(var, False)


class PlusShuffleMode(ShuffleMode):
    def run(self):
        if self._var_set is None:
            return
        self._shuffle_light_group()
        if len(self._shuffle_nodes) > 0:
            for var_name, var_shuffle_nodes in self._shuffle_nodes.items():
                current_node = var_shuffle_nodes[0]
                for node in var_shuffle_nodes[1:]:
                    current_node = nuke.nodes.Merge(operation="plus", inputs=[current_node, node])
                    # merge_node = nuke.createNode("Merge") #TODO remove
                    # merge_node["operation"].setValue("plus")
                    # merge_node.setInput(1, current_node)
                    # merge_node.setInput(0, node)
                    # current_node = merge_node
                current_node["name"].setValue("shuffled_" + var_name)
                self._var_set.active_var(Variable(var_name, current_node))
