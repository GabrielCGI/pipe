import nuke
from common.utils import *
from .LayoutManager import LayoutManager
from .RuleSet import Variable
from .UnpackMode import BACKDROP_MERGE

# ######################################################################################################################

_PREFIX_DOT = "dot_"
_DISTANCE_STEP_MERGE = 2


# ######################################################################################################################


class MergeMode:
    def __init__(self, relations, layout_manager):
        self.__layout_manager = layout_manager
        self.__var_set = None
        self.__relations = relations

    # Setter of the variable set
    def set_var_set(self, var_set):
        self.__var_set = var_set

    # Getter of the  raltions
    def get_relations(self):
        return self.__relations

    def __run_group(self):
        active_vars = self.__var_set.get_active_vars()
        var_by_name = {}

        for var in active_vars:
            var_name = var.get_name()
            if var_name not in var_by_name:
                var_by_name[var_name] = []
            var_by_name[var_name].append(var)

        for var_name, vars in var_by_name.items():
            if len(vars) <= 1: continue
            print(var_name, len(vars))
            vars.sort(key=lambda x: x.get_layer().lower())
            operation = vars[0].get_group_operation()
            if operation is None: continue

            start_node = vars[0].get_node()
            name = vars[0].get_name()
            previous_layer = vars[0].get_layer()
            step = vars[0].get_step() + 1

            previous_node = nuke.nodes.Dot(name=_PREFIX_DOT+previous_layer, inputs=[start_node])
            self.__layout_manager.add_nodes_to_backdrop(BACKDROP_MERGE, [previous_node])
            self.__layout_manager.add_node_layout_relation(start_node, previous_node,
                                                           LayoutManager.POS_RIGHT, _DISTANCE_STEP_MERGE)
            self.__var_set.active_var(vars[0], False)
            for var in vars[1:]:
                self.__var_set.active_var(var, False)
                current_layer = var.get_layer()
                current_node = var.get_node()

                merge_node = nuke.nodes.Merge(operation=str(operation),
                                              inputs=[previous_node,current_node])
                merge_node.setName("merge_" + operation + "_" + current_layer)

                self.__layout_manager.add_nodes_to_backdrop(BACKDROP_MERGE, [merge_node])

                self.__layout_manager.add_node_layout_relation(current_node, merge_node,
                                                               LayoutManager.POS_RIGHT, _DISTANCE_STEP_MERGE)
                previous_node = merge_node

            result_var = Variable(name, previous_node, [], step)
            self.__var_set.active_var(result_var, True)

    # Run the Merge
    def run(self):
        if self.__var_set is None:
            return
        self.__run_group()
        # Iterate through relations
        for rel in self.__relations:
            active_vars = self.__var_set.get_active_vars()[:]
            var_a = None
            var_b = None
            # Retrieve the variables needed to compute the relation
            for var in active_vars:
                if rel.is_valid_for_a(var) and var_a is None and var != var_b:
                    var_a = var
                elif rel.is_valid_for_b(var) and var_b is None and var != var_a:
                    var_b = var


            if var_a is None or var_b is None:
                for var in active_vars:
                    if rel.alias_is_valid_for_a(var) and var_a is None and var != var_b:
                        var_b = var
                    elif rel.alias_is_valid_for_b(var) and var_b is None and var != var_a:
                        var_b = var

            # Abort if variable not found
            if var_a is None or var_b is None:
                continue

            node_a = var_a.get_node()
            node_b = var_b.get_node()
            # Create the graph layout
            dot_node = nuke.nodes.Dot(name=_PREFIX_DOT + var_a.get_name() + rel.get_operation() + var_b.get_name(),
                                      inputs=[node_b])
            self.__layout_manager.add_nodes_to_backdrop(BACKDROP_MERGE, [dot_node])
            var_b.set_node(dot_node)
            result_var = rel.process(var_a, var_b)

            result_var_step = result_var.get_step()

            result_node = result_var.get_node()

            self.__layout_manager.add_nodes_to_backdrop(BACKDROP_MERGE, [result_node])

            self.__layout_manager.add_node_layout_relation(node_b, dot_node,
                                                           LayoutManager.POS_RIGHT,
                                                           (result_var_step - var_b.get_step()) * _DISTANCE_STEP_MERGE)
            self.__layout_manager.add_node_layout_relation(node_a, result_var.get_node(),
                                                           LayoutManager.POS_RIGHT,
                                                           (result_var_step - var_a.get_step()) * _DISTANCE_STEP_MERGE)
            # Set used var to inactive and the new var created to active
            self.__var_set.active_var(var_a, False)
            self.__var_set.active_var(var_b, False)
            self.__var_set.active_var(result_var, True)
