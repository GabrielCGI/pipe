import json
import os.path
import re

from common.utils import *
from .ShuffleMode import ShuffleMode, ShuffleChannelMode
from .MergeMode import MergeMode
from .UnpackMode import UnpackMode, DEFAULT_LAYER_COLOR
from .LayoutManager import LayoutManager
from .RuleSet import VariablesSet, Variable, StartVariable, Relation

# ######################################################################################################################

_NAME_KEY = "name"

_LAYERS_KEY = "layers"
_LAYERS_NAME_KEY = "name"
_LAYERS_RULE_KEY = "rule"
_LAYERS_ALIASES_KEY = "aliases"
_LAYERS_OPTIONS_KEY = "options"
_LAYERS_GROUP_OPERATION_KEY = "group_operation"
_SHUFFLE_KEY = "shuffle"
_SHUFFLE_OPTIONS_KEY = "options"
_MERGE_KEY = "merge"
_MERGE_RULES_KEY = "rules"
_RESULT_MERGE_RULE_KEY = "result"
_A_NODE_MERGE_RULE_KEY = "a"
_B_NODE_MERGE_RULE_KEY = "b"
_OPERATION_MERGE_RULE_KEY = "operation"


# ######################################################################################################################


class AutoCompFactory:
    # Create an Unpack Mode with a json file path that contains a name, a shuffle mode
    # and the path to the merge mode rule set json file
    @staticmethod
    def get_unpack_mode(path):
        layout_manager = LayoutManager()
        # Parse Rule Set
        rule_set_data = AutoCompFactory.__parse_rule_set(path)
        if _SHUFFLE_KEY not in rule_set_data or _LAYERS_KEY not in rule_set_data or \
                _MERGE_KEY not in rule_set_data or _NAME_KEY not in rule_set_data: return None
        # Shuffle
        shuffle_mode = ShuffleMode(layout_manager, rule_set_data[_SHUFFLE_KEY])
        # Variable Set
        var_set = AutoCompFactory.__get_var_set(rule_set_data[_LAYERS_KEY])
        if var_set is None: return None
        # Relations
        merge_mode = AutoCompFactory.__get_merge_mode(rule_set_data[_MERGE_KEY], layout_manager)
        if merge_mode is None: return None
        return UnpackMode(path, rule_set_data[_NAME_KEY], var_set, shuffle_mode, merge_mode, layout_manager)

    # Create an Unpack Mode to shuffle only one layer
    @staticmethod
    def shuffle_layer(path, shot_path, layers):
        layout_manager = LayoutManager()
        # Parse Rule Set
        rule_set_data = AutoCompFactory.__parse_rule_set(path)
        if _SHUFFLE_KEY not in rule_set_data or _LAYERS_KEY not in rule_set_data or \
                _MERGE_KEY not in rule_set_data or _NAME_KEY not in rule_set_data: return None
        # Shuffle
        shuffle_mode = ShuffleMode(layout_manager)
        # Variable Set
        var_set = AutoCompFactory.__get_var_set(rule_set_data[_LAYERS_KEY], layers[:])
        if var_set is None: return None
        # Relations
        merge_mode = AutoCompFactory.__get_merge_mode({_MERGE_RULES_KEY: []}, layout_manager)
        if merge_mode is None: return None
        unpack_mode = UnpackMode(path, rule_set_data[_NAME_KEY],
                                 var_set, shuffle_mode, MergeMode([], layout_manager), layout_manager)
        unpack_mode.scan_layers(shot_path, layers)
        unpack_mode.unpack(shot_path)

    # Create an Unpack Mode to shuffle channels of a layer
    @staticmethod
    def shuffle_channel_mode(read_node, channels):
        layout_manager = LayoutManager()
        # Shuffle
        shuffle_mode = ShuffleChannelMode(channels, layout_manager)
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
        shuffle_mode.run(True)
        # Organize all the nodes
        layout_manager.build_layout_node_graph()
        # Organize all the backdrops
        layout_manager.build_layout_backdrops()

    @staticmethod
    def __parse_rule_set(path):
        with open(path, "r") as f:
            json_data = f.read()
        try:
            return json.loads(json_data)
        except Exception as e:
            print("Error while parsing " + path + " :\n" + str(e))
            return None

    # Get the Variable Set according to the layers config data
    @staticmethod
    def __get_var_set(start_vars_data, layer_filter_arr=None):
        start_vars = []
        order=0
        # Scan for start variables
        for order, start_var_data in enumerate(start_vars_data):
            # Ignore if start variable has not name or rule
            if _LAYERS_NAME_KEY not in start_var_data or \
                    _LAYERS_RULE_KEY not in start_var_data or \
                    _LAYERS_OPTIONS_KEY not in start_var_data :
                continue
            rule = start_var_data[_LAYERS_RULE_KEY]
            layer_caught = None
            if layer_filter_arr is not None:
                for layer_filter in layer_filter_arr:
                    if re.match(rule,layer_filter):
                        layer_caught = layer_filter
                        break
                if layer_caught is not None:
                    layer_filter_arr.remove(layer_caught)
                else: continue

            aliases = start_var_data[_LAYERS_ALIASES_KEY] if _LAYERS_ALIASES_KEY in start_var_data else []
            group_operation = start_var_data[_LAYERS_GROUP_OPERATION_KEY] \
                if _LAYERS_GROUP_OPERATION_KEY in start_var_data else None
            start_vars.append(
                StartVariable(start_var_data[_LAYERS_NAME_KEY],
                              layer_caught,
                              rule,
                              aliases,
                              order,
                              start_var_data[_LAYERS_OPTIONS_KEY],
                              group_operation))

        if layer_filter_arr is not None:
            for layer in layer_filter_arr:
                order+=1
                start_vars.append(
                    StartVariable(layer,
                                  layer,
                                  r"^"+layer+r"$",
                                  [],
                                  order,
                                  {"color": DEFAULT_LAYER_COLOR},
                                  None))

        # Error if no start variables
        if len(start_vars) == 0:
            return None
        return VariablesSet(start_vars)

    # Build the Merge by parsing the rule set json file
    @staticmethod
    def __get_merge_mode(merge_data, layout_manager):
        if _MERGE_RULES_KEY not in merge_data:
            return None
        relations = []
        for rel_data in merge_data[_MERGE_RULES_KEY]:
            # Ignore if relation has not node a node b or operation
            if _A_NODE_MERGE_RULE_KEY not in rel_data or \
                    _B_NODE_MERGE_RULE_KEY not in rel_data or \
                    _OPERATION_MERGE_RULE_KEY not in rel_data:
                print("### Warning : AutoCompFactory.__get_merge_mode(...)")
                print("### Warning : Bad relation definition :")
                print("### Warning : " + str(rel_data))
                continue
            node_a = rel_data[_A_NODE_MERGE_RULE_KEY]
            node_b = rel_data[_B_NODE_MERGE_RULE_KEY]
            operation = rel_data[_OPERATION_MERGE_RULE_KEY]
            # Retrieve result_name if exists
            if _RESULT_MERGE_RULE_KEY in rel_data:
                result_name = rel_data[_RESULT_MERGE_RULE_KEY]
                relations.append(Relation(node_a, node_b, operation, result_name))
            else:
                relations.append(Relation(node_a, node_b, operation))
        return MergeMode(relations, layout_manager)
