import re
import nuke


class VariablesSet:
    def __init__(self, rule_vars):
        self.__start_vars = rule_vars
        self.__active_vars = []

    # Getter of the start variables
    def get_start_vars(self):
        return self.__start_vars

    # Getter of the active variables
    def get_active_vars(self):
        return self.__active_vars

    # Getter of the start variables valid for a specific layer name
    def get_start_variable_valid_for(self, layer_name):
        for start_var in self.__start_vars:
            if start_var.is_rule_valid(layer_name):
                return start_var
        return None

    # Set a variable to active or inactive
    def active_var(self, var, active=True):
        if active:
            self.__active_vars.append(var)
        else:
            self.__active_vars.remove(var)

class Variable:
    def __init__(self, name, node, step=0):
        self.__name = name
        self._node = node
        self.__step = step

    # Getter of the name of the variable
    def get_name(self):
        return self.__name

    # Getter of the node of the variable
    def get_node(self):
        return self._node

    # Getter of the step of the variable (needed when the merge section is running to know the layout order)
    def get_step(self):
        return self.__step

    # Setter of the node of the variable
    def set_node(self, node):
        self._node = node

    # To String method
    def __str__(self):
        return self.__name


class StartVariable(Variable):
    def __init__(self, name, rule, order, options):
        Variable.__init__(self, name, None)
        self.__rule = rule
        self.__order = order
        self.__options = options

    # Get the order of the start variable
    def get_order(self):
        return self.__order

    # Get the option of the start variable
    def get_option(self, option):
        if option not in self.__options:
            return None
        return self.__options[option]

    # Check of a layer name is valid for the starrt variable
    def is_rule_valid(self, layer_name):
        return re.match(self.__rule, layer_name) is not None


class Relation:
    def __init__(self, name_a, name_b, operation, result_name=None):
        self.__name_a = name_a
        self.__name_b = name_b
        self.__operation = operation
        self.__result_name = result_name

    # To String method
    def __str__(self):
        string = self.__name_a + " " + self.__operation + " " + self.__name_b
        if self.__result_name is not None:
            string += " -> " + self.__result_name
        return string

    # Check if the variable is valid for the relation A variable
    def is_valid_for_a(self, var):
        return self.__name_a == var.get_name()

    # Check if the variable is valid for the relation B variable
    def is_valid_for_b(self, var):
        return self.__name_b == var.get_name()

    # Getter of the merge operation
    def get_operation(self):
        return self.__operation

    # Process the relation by creating a merge node with the correct operation
    def process(self, var_a, var_b):
        merge_node = nuke.nodes.Merge(operation=str(self.__operation), inputs=[var_b.get_node(), var_a.get_node()])
        merge_node.setName(self.__name_a+"_"+self.__operation+"_"+self.__name_b)
        step = max(var_a.get_step(),var_b.get_step())+1
        if self.__result_name is None:
            return Variable("", merge_node, step)
        return Variable(self.__result_name, merge_node, step)
