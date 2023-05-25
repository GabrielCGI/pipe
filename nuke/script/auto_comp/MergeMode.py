import nuke
from common.utils import *
from .LayoutManager import LayoutManager
from .UnpackMode import BACKDROP_MERGE


# ######################################################################################################################

_PREFIX_DOT = "dot_"
_DISTANCE_STEP_MERGE = 1

# ######################################################################################################################


class MergeMode:
    def __init__(self, relations, layout_manager):
        self.__layout_manager = layout_manager
        self.__var_set = None
        self.__relations = relations

    def set_var_set(self, var_set):
        self.__var_set = var_set

    def get_relations(self):
        return self.__relations

    def run(self):
        if self.__var_set is None:
            return

        for rel in self.__relations:
            active_vars = self.__var_set.get_active_vars()
            var_a = None
            var_b = None
            for var in active_vars:
                if rel.is_valid_for_a(var) and var_a is None:
                    var_a= var
                elif rel.is_valid_for_b(var) and var_b is None:
                    var_b= var
            if var_a is None or var_b is None:
                continue

            node_a = var_a.get_node()
            node_b = var_b.get_node()
            dot_node = nuke.nodes.Dot(name=_PREFIX_DOT + var_a.get_name() + rel.get_operation()+ var_b.get_name(),
                                      inputs=[node_b])
            self.__layout_manager.add_nodes_to_backdrop(BACKDROP_MERGE, [dot_node])
            var_b.set_node(dot_node)
            result_var = rel.process(var_a, var_b)

            result_var_step = result_var.get_step()
            result_node = result_var.get_node()

            self.__layout_manager.add_nodes_to_backdrop(BACKDROP_MERGE, [result_node])

            self.__layout_manager.add_node_layout_relation(node_b, dot_node,
                                                           LayoutManager.POS_RIGHT,
                                                           result_var_step - var_b.get_step() * _DISTANCE_STEP_MERGE)
            self.__layout_manager.add_node_layout_relation(node_a, result_var.get_node(),
                                                           LayoutManager.POS_RIGHT,
                                                           result_var_step - var_a.get_step() * _DISTANCE_STEP_MERGE)
            self.__var_set.active_var(var_a, False)
            self.__var_set.active_var(var_b, False)
            self.__var_set.active_var(result_var, True)
