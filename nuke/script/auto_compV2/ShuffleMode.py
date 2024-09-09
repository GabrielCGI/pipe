import nuke
from common.utils import *
from .RuleSet import Variable
from .LayoutManager import LayoutManager
from .UnpackMode import BACKDROP_LAYER, BACKDROP_MERGE, BACKDROP_LAYER_SHUFFLE

# ######################################################################################################################

_SHUFFLE_LAYER_KEY = "shuffle_layer"
_PREFIX_SHUFFLE = "shuffle_"
_PREFIX_MERGE_SHUFFLE = "merge_shuffle_"
_PREFIX_MERGE_SHUFFLED = "shuffled_"
_PREFIX_DOT = "dot_"
_DISTANCE_COLUMN_SHUFFLE = 2
_DISTANCE_READ_TO_SHUFFLE = 1.7
_HEIGHT_COLUMN_SHUFFLE = 3
_DISTANCE_OUTPUT_SHUFFLE = 1.7
_PERCENT_HEIGHT_SHUFFLE = 1/4.0
_EXTRA_CHANNELS = ["emission", "emission_indirect"]


# ######################################################################################################################


class ShuffleMode:
    @staticmethod
    def get_light_group_channels(node):
        """
        Get all the light group channels of a node
        :param node
        :return: channels
        """
        detailed_channels = node.channels()
        visited_channels = []
        channels = []
        for channel in detailed_channels:
            channel_split = channel.split(".")[0]
            if (channel_split.startswith("C_") or channel_split in _EXTRA_CHANNELS) and channel_split not in visited_channels:
                channels.append(channel_split)
                visited_channels.append(channel_split)
        return channels

    @staticmethod
    def get_present_channels(read_node):
        """
        Get all the channels shuffled of a read node in the graph
        :param read_node:
        :return:
        """
        child_nodes = []

        def __check_node(root_node, current):
            try:
                inputs = current.inputs()
                for i in range(inputs):
                    input_node = current.input(i)
                    if input_node is None: continue
                    if input_node == read_node or input_node in child_nodes:
                        child_nodes.append(root_node)
                        break
                    else:
                        __check_node(root_node, input_node)
            except Exception as e:

                print("%s.inputs() doesn't exist"%current)
                print (e.message, e.args)

        for node in nuke.allNodes("Shuffle2"):
            __check_node(node, node)

        return map(lambda x: x.knob("in1").value(), child_nodes)

    def __init__(self, layout_manager, shuffle_data=None):
        """
        Constructor
        :param layout_manager
        :param shuffle_data
        """
        self._layout_manager = layout_manager
        self._var_set = None
        self.__shuffle_layer_option = shuffle_data[_SHUFFLE_LAYER_KEY] if shuffle_data is not None else None
        self._var_by_name = {}
        self._shuffle_nodes = {}
        self._output_nodes = {}

    def set_var_set(self, var_set):
        """
        Setter of the variable set
        :param var_set
        :return:
        """
        self._var_set = var_set

    def _get_channels(self, node_var):
        """
        Get the channels to shuffle
        :param node_var
        :return: channels
        """
        return ShuffleMode.get_light_group_channels(node_var)

    def run(self, only_core_shuffle = False):
        """
        Run the Shuffle by shuffling variables, merging them and creating correct output nodes
        :param only_core_shuffle:
        :return:
        """
        if self._var_set is None:
            return
        self.__shuffle_vars(only_core_shuffle)
        self.__merge_shuffle(only_core_shuffle)
        if not only_core_shuffle:
            self.__output_shuffle()

    def __shuffle_vars(self, only_core_shuffle):
        """
        Launch shuffle on all the variables
        :param only_core_shuffle
        :return:
        """
        for var in self._var_set.get_active_vars()[:]:
            self._var_by_name[var.get_layer()] = var
            self._shuffle_light_group(var, only_core_shuffle)

    def _shuffle_light_group(self, var, only_core_shuffle):
        """
        Shuffle a Variable if it is in layer to shuffle
        :param var
        :param only_core_shuffle
        :return:
        """
        name_var = var.get_name()
        node_var = var.get_node()
        layer = var.get_layer()
        if layer is None: layer = name_var
        # If the layer to shuffle option exists and doesn't contain the current var_name don't shuffle
        if self.__shuffle_layer_option is not None and name_var not in self.__shuffle_layer_option:
            self._var_set.active_var(var, False)
            self._output_nodes[layer] = (var, node_var, 0)
            return False
        # Backdrops name
        backdrop_longname = ".".join([BACKDROP_LAYER, layer])
        shuffle_backdrop_longname = ".".join([backdrop_longname, BACKDROP_LAYER_SHUFFLE])

        # If we want intermediate nodes we create it otherwise set to None
        if only_core_shuffle:
            dot_node = None
        else:
            init_dot = nuke.nodes.Dot(name=_PREFIX_DOT + layer, inputs=[node_var])

            self._layout_manager.add_nodes_to_backdrop(backdrop_longname, [init_dot])
            self._layout_manager.add_backdrop_option(shuffle_backdrop_longname, "margin_bottom", 56)
            self._layout_manager.add_backdrop_option(shuffle_backdrop_longname, "font_size", 30)
            self._layout_manager.add_node_layout_relation(node_var, init_dot, LayoutManager.POS_RIGHT,
                                                          _DISTANCE_READ_TO_SHUFFLE / 2.0)
            dot_node = nuke.nodes.Dot(name=_PREFIX_DOT + layer, inputs=[init_dot])
            self._layout_manager.add_nodes_to_backdrop(backdrop_longname, [dot_node])
            self._layout_manager.add_node_layout_relation(init_dot, dot_node, LayoutManager.POS_TOP,
                                                          _HEIGHT_COLUMN_SHUFFLE)

        # Get the channels to shuffle
        channels = self._get_channels(node_var)

        # Unselect all to prevent nuke auto linking
        for node in nuke.selectedNodes():
            node.setSelected(False)

        lg_channels = []
        # for each channel create input and connect to the last to create a chain
        for channel in channels:
            if len(lg_channels) == 0:
                dist = _DISTANCE_READ_TO_SHUFFLE / 2.0
            else:
                dist = _DISTANCE_COLUMN_SHUFFLE

            prev_node = dot_node
            if prev_node is None:
                dot_node = nuke.nodes.Dot(name=_PREFIX_DOT + layer)
            else:
                dot_node = nuke.nodes.Dot(name=_PREFIX_DOT + layer, inputs=[prev_node])
                self._layout_manager.add_node_layout_relation(prev_node, dot_node, LayoutManager.POS_RIGHT, dist)

            self._layout_manager.add_nodes_to_backdrop(shuffle_backdrop_longname, [dot_node])

            lg_channels.append((channel, dot_node))

        # Shuffle all the inputs created and set the varaible to unactive
        if len(lg_channels) > 0:
            self._shuffle_nodes[layer] = []
            for lg_channel, node in lg_channels:
                self.__shuffle_channel(node, var, lg_channel, shuffle_backdrop_longname)
            self._var_set.active_var(var, False)

    def __shuffle_channel(self, input_node, var, channel, shuffle_backdrop_longname):
        """
        Shuffle a Channel
        :param input_node
        :param var
        :param channel
        :param shuffle_backdrop_longname
        :return:
        """
        layer_var = var.get_layer()
        shuffle_node = nuke.createNode("Shuffle2")
        shuffle_node["in1"].setValue(channel)
        shuffle_node["postage_stamp"].setValue(True)
        shuffle_node.setName(_PREFIX_SHUFFLE + layer_var + "_" + channel.replace("C_", ""))
        shuffle_node.setInput(0, input_node)
        self._layout_manager.add_nodes_to_backdrop(shuffle_backdrop_longname, [shuffle_node])
        self._layout_manager.add_node_layout_relation(input_node, shuffle_node, LayoutManager.POS_BOTTOM,
                                                      _HEIGHT_COLUMN_SHUFFLE * _PERCENT_HEIGHT_SHUFFLE)
        self._shuffle_nodes[layer_var].append(shuffle_node)

    def __merge_shuffle(self, only_core_shuffle):
        """
        Merge the shuffled nodes for each variable
        :param only_core_shuffle
        :return:
        """
        if len(self._shuffle_nodes)== 0: return

        half_height_col = _HEIGHT_COLUMN_SHUFFLE * (1 - _PERCENT_HEIGHT_SHUFFLE)

        for var_layer, var_shuffle_nodes in self._shuffle_nodes.items():
            shuffle_backdrop_longname = ".".join([BACKDROP_LAYER, var_layer, BACKDROP_LAYER_SHUFFLE])
            first = True
            current_node = None
            # For each shuffle nodes of the variable we create a merge node
            # (or a dot if first or if we want only core nodes)
            nb_var_shuffle_nodes = len(var_shuffle_nodes)
            for i, node in enumerate(var_shuffle_nodes):
                name_node = _PREFIX_MERGE_SHUFFLED + var_layer if i == nb_var_shuffle_nodes-1 else None
                if first and not only_core_shuffle:
                    first = False
                    merge_node = nuke.nodes.Dot(name=_PREFIX_DOT + var_layer if name_node is None else name_node,
                                                inputs=[node])
                else:
                    merge_node = nuke.nodes.Merge(
                        name=_PREFIX_MERGE_SHUFFLE + var_layer if name_node is None else name_node,
                        operation="plus", A="rgb", inputs=[current_node, node])
                self._layout_manager.add_nodes_to_backdrop(shuffle_backdrop_longname, [merge_node])
                self._layout_manager.add_node_layout_relation(node, merge_node, LayoutManager.POS_BOTTOM,
                                                              half_height_col)
                current_node = merge_node

            # Add the last created node the the output node
            self._output_nodes[var_layer] = (self._var_by_name[var_layer], current_node, len(var_shuffle_nodes))

    def __output_shuffle(self):
        """
        Compute the output of the shuffle
        :return:
        """
        max_len = 0
        # Get the max distance at which shuffles end
        for var, output_node, len_shuffle in self._output_nodes.values():
            if len_shuffle > max_len: max_len = len_shuffle

        for layer_name, output_node_data in self._output_nodes.items():
            var, output_node, len_shuffle = output_node_data
            # Compute the correct distance to place the end node
            diff_len = max_len - len_shuffle
            if max_len == 0:
                dist = _DISTANCE_OUTPUT_SHUFFLE
            else:
                if len_shuffle != 0:
                    dist = diff_len * _DISTANCE_COLUMN_SHUFFLE + _DISTANCE_OUTPUT_SHUFFLE
                else:
                    dist = (max_len - 1) * _DISTANCE_COLUMN_SHUFFLE + _DISTANCE_READ_TO_SHUFFLE + _DISTANCE_OUTPUT_SHUFFLE
            # Create a end dot to the correct distance from the output node
            dot_node = nuke.nodes.Dot(name=_PREFIX_DOT + layer_name, inputs=[output_node])
            self._layout_manager.add_nodes_to_backdrop(BACKDROP_MERGE, [dot_node])
            self._layout_manager.add_node_layout_relation(output_node, dot_node,
                                                          LayoutManager.POS_RIGHT, dist)
            var.set_node(dot_node)
            self._var_set.active_var(var)


class ShuffleChannelMode(ShuffleMode):
    """
    Shuffle Mode to only shuffle specific channel
    """
    def __init__(self, channels, layout_manager):
        """
        Constructor
        :param channels
        :param layout_manager
        """
        ShuffleMode.__init__(self, layout_manager)
        self.__channels = channels

    def _get_channels(self, node_var):
        """
        Get the channels to shuffle
        :param node_var
        :return: channels
        """
        node_channels = map(lambda x: x.split(".")[0], node_var.channels())
        channels = []
        for channel in self.__channels:
            if channel in node_channels:
                channels.append(channel)
        return channels
