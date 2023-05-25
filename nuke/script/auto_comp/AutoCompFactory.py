import json
import os.path

from common.utils import *
from .ShuffleMode import ShuffleMode
from .MergeMode import MergeMode
from .UnpackMode import UnpackMode
from .LayoutManager import LayoutManager
from .RuleSet import VariablesSet, Variable, StartVariable, Relation

# ######################################################################################################################

_NAME_KEY = "name"

_LAYERS_KEY = "layers"
_LAYERS_NAME_KEY = "name"
_LAYERS_RULE_KEY = "rule"
_LAYERS_OPTIONS_KEY = "options"
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
    def get_simple_shuffle_layer_mode(path, layer):
        layout_manager = LayoutManager()
        # Parse Rule Set
        rule_set_data = AutoCompFactory.__parse_rule_set(path)
        if _SHUFFLE_KEY not in rule_set_data or _LAYERS_KEY not in rule_set_data or \
                _MERGE_KEY not in rule_set_data or _NAME_KEY not in rule_set_data: return None
        # Shuffle
        shuffle_mode = ShuffleMode(layout_manager, rule_set_data[_SHUFFLE_KEY])
        # Variable Set
        var_set = AutoCompFactory.__get_var_set(rule_set_data[_LAYERS_KEY], layer)
        if var_set is None: return None
        # Relations
        merge_mode = AutoCompFactory.__get_merge_mode({_MERGE_RULES_KEY: []}, layout_manager)
        if merge_mode is None: return None
        return UnpackMode(path, rule_set_data[_NAME_KEY], var_set, shuffle_mode, merge_mode, layout_manager)

    @staticmethod
    def __parse_rule_set(path):
        with open(path, "r") as f:
            json_data = f.read()
        try:
            return json.loads(json_data)
        except Exception as e:
            print("Error while parsing " + path + " :\n" + str(e))
            return None

    @staticmethod
    def __get_var_set(start_vars_data, layer_filter=None):
        start_vars = []
        # Scan for start variables
        for order, start_var_data in enumerate(start_vars_data):
            # Ignore if start variable has not name or rule
            if _LAYERS_NAME_KEY not in start_var_data or \
                    _LAYERS_RULE_KEY not in start_var_data or \
                    _LAYERS_OPTIONS_KEY not in start_var_data:
                continue
            name = start_var_data[_LAYERS_NAME_KEY]
            if layer_filter is not None and name != layer_filter:
                continue
            start_vars.append(
                StartVariable(start_var_data[_LAYERS_NAME_KEY],
                              start_var_data[_LAYERS_RULE_KEY],
                              order,
                              start_var_data[_LAYERS_OPTIONS_KEY]))
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
