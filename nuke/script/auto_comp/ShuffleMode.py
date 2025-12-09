import nuke
from common.utils import *
from .LayoutManager import LayoutManager

# ######################################################################################################################

BACKDROP_LAYER = "LAYER"
BACKDROP_MERGE = "MERGE"
BACKDROP_LAYER_SHUFFLE = "SHUFFLE"

_SHUFFLE_LAYER_KEY = "shuffle_layer"
_PREFIX_SHUFFLE = "shuffle_"
_PREFIX_MERGE_SHUFFLE = "merge_shuffle_"
_PREFIX_MERGE_SHUFFLED = "shuffled_"
_PREFIX_DOT = "dot_"
_DISTANCE_CLOSE_HEIGHT = 0.25
_DISTANCE_FIRST_MERGE = 1.0
_DISTANCE_COLUMN_SHUFFLE = 1.75
_DISTANCE_READ_TO_SHUFFLE = 1.7
_DISTANCE_FIRST_SHUFFLE = 1.0
_HEIGHT_COLUMN_SHUFFLE = 2
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

        return [node['in1'].value() for node in child_nodes]

    def __init__(self, layout_manager, shuffle_data=None):
        """
        Constructor
        :param layout_manager
        :param shuffle_data
        """
        self._layout_manager: LayoutManager = layout_manager
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
        self.first_node = nuke.nodes.Dot(inputs=[node_var])
        prev_node = self.first_node
        self._layout_manager.add_node_layout_relation(node_var, prev_node, LayoutManager.POS_BOTTOM, _DISTANCE_READ_TO_SHUFFLE / 2.0)
        for i, channel in enumerate(channels):
            if i == 0:
                dist = _DISTANCE_FIRST_SHUFFLE
            else:
                dist = _DISTANCE_COLUMN_SHUFFLE
            dot_node = nuke.nodes.Dot(inputs=[prev_node])
            self._layout_manager.add_node_layout_relation(prev_node, dot_node, LayoutManager.POS_LEFT, dist)
            prev_node = dot_node
            lg_channels.append((channel, dot_node))

        # Shuffle all the inputs created and set the varaible to unactive
        if len(lg_channels) > 0:
            self._shuffle_nodes[layer] = []
            for lg_channel, node in lg_channels:
                layer_var = var.get_layer()
                shuffle_node = self.__shuffle_channel(node, lg_channel)
                self._shuffle_nodes[layer_var].append(shuffle_node)

            self._var_set.active_var(var, False)

    def __shuffle_channel(
            self,
            input_node,
            channel,
            position=LayoutManager.POS_BOTTOM,
            dist=_HEIGHT_COLUMN_SHUFFLE * _PERCENT_HEIGHT_SHUFFLE) -> nuke.Node:
        """
        Shuffle a Channel
        :param input_node
        :param var
        :param channel
        :param shuffle_backdrop_longname
        :return:
        """
        shuffle_node = nuke.nodes.Shuffle2(inputs=[input_node])
        shuffle_node["in1"].setValue(channel)
        shuffle_node["out1"].setValue("rgb")
        shuffle_node['label'].setText('[value in1]')
        self._layout_manager.add_node_layout_relation(
            input_node,
            shuffle_node,
            position,
            dist)
        return shuffle_node

    def __merge_shuffle(self, only_core_shuffle=False):
        """
        Merge the shuffled nodes for each variable
        :param only_core_shuffle
        :return:
        """
        if len(self._shuffle_nodes)== 0: return

        low_height_col = _DISTANCE_CLOSE_HEIGHT
        high_height_col = _DISTANCE_FIRST_MERGE
        for var_layer, var_shuffle_nodes in self._shuffle_nodes.items():
            last_merge = None
            # For each shuffle nodes of the variable we create a merge node
            # (or a dot if first or if we want only core nodes)
            for i, node in enumerate(var_shuffle_nodes):
                up_node = nuke.nodes.Unpremult(inputs=[node])
                self._layout_manager.add_node_layout_relation(
                    node,
                    up_node,
                    LayoutManager.POS_BOTTOM,
                    low_height_col + 0.1
                )
                if i == 0:
                    merge_node = up_node
                else:
                    dot = nuke.nodes.Dot(inputs=[up_node])
                    if i == 1:
                        merge_distance = high_height_col
                    else:
                        merge_distance = low_height_col
                    self._layout_manager.add_node_layout_relation(
                        up_node,
                        dot,
                        LayoutManager.POS_BOTTOM,
                        high_height_col + (i-1)*merge_distance
                    )
                    merge_node = nuke.nodes.Merge2(
                        operation="plus",
                        A="rgb",
                        inputs=[last_merge, dot]
                    )
                    self._layout_manager.add_node_layout_relation(
                        last_merge,
                        merge_node,
                        LayoutManager.POS_BOTTOM,
                        merge_distance
                    )
                last_merge = merge_node

            # Add the last created node the the output node
            self._output_nodes[var_layer] = (self._var_by_name[var_layer], last_merge, len(var_shuffle_nodes))
            
        # Add shuffle and unpremult node at the end after the last merge
        last_dot = nuke.nodes.Dot(inputs=[last_merge])
        self._layout_manager.add_node_layout_relation(
            last_merge,
            last_dot,
            LayoutManager.POS_BOTTOM,
            _DISTANCE_READ_TO_SHUFFLE / 2.0
        )
        last_shuffle: nuke.Node = nuke.createNode("Shuffle2")
        last_shuffle.setInput(1, last_dot)
        last_shuffle.setInput(0, self.first_node)
        last_shuffle["in1"].setValue("rgb")
        last_shuffle["out1"].setValue("rgb")
        last_shuffle["fromInput1"].setValue("A")
        self._layout_manager.add_node_layout_relation(
            last_dot,
            last_shuffle,
            LayoutManager.POS_RIGHT,
            _DISTANCE_FIRST_SHUFFLE)
        last_up = nuke.nodes.Premult(inputs=[last_shuffle])
        self._layout_manager.add_node_layout_relation(
            last_shuffle,
            last_up,
            LayoutManager.POS_BOTTOM,
            low_height_col
        )

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
