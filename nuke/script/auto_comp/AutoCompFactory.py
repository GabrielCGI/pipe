from common.utils import *
# from .ShuffleMode import ShuffleChannelMode
from .LayoutManager import LayoutManager
from .RuleSet import VariablesSet, StartVariable


class AutoCompFactory:

    @staticmethod
    def shuffle_channel_mode(read_node, channels, horizontal_padding=1.0, vertical_padding=1.0):
        """
        Create an Unpack Mode to shuffle channels of a layer
        :param read_node
        :param channels
        :return:
        """
        from . import ShuffleMode
        import importlib
        importlib.reload(ShuffleMode)
        
        layout_manager = LayoutManager()
        # Shuffle
        shuffle_mode = ShuffleMode.ShuffleChannelMode(channels, layout_manager, horizontal_padding=horizontal_padding, vertical_padding=vertical_padding)
        var_set = VariablesSet([])
        # name, layer, rule, aliases, order, options, group_operation
        read_name = read_node.name()
        start_var = StartVariable(read_name,read_name)
        start_var.set_node(read_node)
        var_set.active_var(start_var)
        shuffle_mode.set_var_set(var_set)

        # Retrieve the bounding box of the current graph to place correctly incoming graph
        layout_manager.compute_current_bbox_graph()
        # Shuffle those layers if needed
        shuffle_mode.run()
        # Organize all the nodes
        layout_manager.build_layout_node_graph()