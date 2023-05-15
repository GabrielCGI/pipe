import json
import os.path

from common.utils import *
from .ShuffleMode import PlusShuffleMode
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
_SHUFFLE_MODE_KEY = "shuffle_mode"
_SHUFFLE_LAYER_KEY = "shuffle_layer"
_MERGE_KEY = "merge"
_MERGE_RULES_KEY = "rules"
_RESULT_MERGE_RULE_KEY = "result"
_A_NODE_MERGE_RULE_KEY = "a"
_B_NODE_MERGE_RULE_KEY = "b"
_OPERATION_MERGE_RULE_KEY = "operation"


# ######################################################################################################################


class AutoCompFactory:
    # Create an Unpack Node with a json file path that contains a name, a shuffle mode
    # and the path to the merge mode rule set json file
    @staticmethod
    def get_unpack_mode(path):
        layout_manager = LayoutManager()
        # Parse Rule Set
        rule_set_data = AutoCompFactory.__parse_rule_set(path)
        if _SHUFFLE_KEY not in rule_set_data or _LAYERS_KEY not in rule_set_data or \
                _MERGE_KEY not in rule_set_data or _NAME_KEY not in rule_set_data: return None
        # Shuffle
        shuffle_data = rule_set_data[_SHUFFLE_KEY]
        if _SHUFFLE_MODE_KEY not in shuffle_data or _SHUFFLE_LAYER_KEY not in shuffle_data: return None
        shuffle_mode = eval(shuffle_data[_SHUFFLE_MODE_KEY])(shuffle_data[_SHUFFLE_LAYER_KEY])
        # Variable Set
        var_set = AutoCompFactory.__get_start_vars(rule_set_data[_LAYERS_KEY])
        if var_set is None: return None
        # Relations
        merge_mode = AutoCompFactory.__get_merge_mode(rule_set_data[_MERGE_KEY])
        if merge_mode is None: return None
        return UnpackMode(rule_set_data[_NAME_KEY], var_set, shuffle_mode, merge_mode, layout_manager)

    @staticmethod
    def __parse_rule_set(path):
        with open(path, "r") as file:
            json_data = file.read()
        try:
            return json.loads(json_data)
        except Exception as e:
            print("Error while parsing " + path + " :\n" + str(e))
            return None

    @staticmethod
    def __get_start_vars(start_vars_data):
        start_vars = []
        # Scan for start variables
        for start_var_data in start_vars_data:
            # Ignore if start variable has not name or rule
            if _LAYERS_NAME_KEY not in start_var_data or \
                    _LAYERS_RULE_KEY not in start_var_data or \
                    _LAYERS_OPTIONS_KEY not in start_var_data:
                continue
            start_vars.append(
                StartVariable(start_var_data[_LAYERS_NAME_KEY],
                              start_var_data[_LAYERS_RULE_KEY],
                              start_var_data[_LAYERS_OPTIONS_KEY]))
        # Error if no start variables
        if len(start_vars) == 0:
            return None
        return VariablesSet(start_vars)

    # Build the Merge by parsing the rule set json file
    @staticmethod
    def __get_merge_mode(merge_data):
        if _MERGE_RULES_KEY not in merge_data:
            return None
        relations_data = merge_data[_MERGE_RULES_KEY]
        relations = []
        for order, rels_order_data in enumerate(relations_data):
            relations.insert(order, [])
            for rel_data in rels_order_data:
                # Ignore if relation has not node a node b or operation
                if _A_NODE_MERGE_RULE_KEY not in rel_data or \
                        _B_NODE_MERGE_RULE_KEY not in rel_data or \
                        _OPERATION_MERGE_RULE_KEY not in rel_data:
                    continue
                node_a = rel_data[_A_NODE_MERGE_RULE_KEY]
                node_b = rel_data[_B_NODE_MERGE_RULE_KEY]
                operation = rel_data[_OPERATION_MERGE_RULE_KEY]
                # Retrieve result_name if exists
                if _RESULT_MERGE_RULE_KEY in rel_data:
                    result_name = rel_data[_RESULT_MERGE_RULE_KEY]
                    relations[order].append(Relation(node_a, node_b, operation, order, result_name))
                else:
                    relations[order].append(Relation(node_a, node_b, operation, order))
        return MergeMode(relations)
