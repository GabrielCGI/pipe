from abc import ABCMeta, abstractmethod
import nuke
from common.utils import *
from .RuleSet import Variable


class ShuffleMode:
    __metaclass__ = ABCMeta

    def __init__(self, shuffle_layer_option):
        self._var_set = None
        self.__shuffle_layer_option = shuffle_layer_option
        self._shuffle_nodes = {}

    def set_var_set(self, var_set):
        self._var_set = var_set

    @abstractmethod
    def run(self):
        pass

    def _shuffle_light_group(self):
        to_deactivate = []
        for var in self._var_set.get_active_vars():
            name_var = var.get_name()
            if name_var not in self.__shuffle_layer_option:
                continue
            node_var = var.get_node()
            dot_node_var = nuke.createNode("Dot")
            dot_node_var.setInput(0, node_var)
            detailed_channels = node_var.channels()
            lg_channels = []
            for channel in detailed_channels:
                channel_split = channel.split(".")[0]
                if channel_split.startswith("RGBA_") and channel_split not in lg_channels:
                    lg_channels.append(channel_split)
            if len(lg_channels) > 0:
                self._shuffle_nodes[name_var] = []
                for lg_channel in lg_channels:
                    shuffle_node = nuke.createNode("Shuffle2")
                    shuffle_node["in1"].setValue(lg_channel)
                    shuffle_node.setInput(0, dot_node_var)
                    self._shuffle_nodes[name_var].append(shuffle_node)
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
