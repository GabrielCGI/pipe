import re
import nuke


class VariablesSet:
    def __init__(self, rule_vars):
        self.__start_vars = rule_vars
        self.__active_vars = []

    def get_start_vars(self):
        return self.__start_vars

    def get_active_vars(self):
        return self.__active_vars

    def get_start_variable_valid_for(self, layer_name):
        for start_var in self.__start_vars:
            if start_var.is_rule_valid(layer_name):
                return start_var
        return None

    def active_var(self, var, active=True):
        if active:
            self.__active_vars.append(var)
        else:
            self.__active_vars.remove(var)


# Can a Start Variable or the result of a valid Relation
class Variable:
    def __init__(self, name, node):
        self.__name = name
        self._node = node

    def get_name(self):
        return self.__name

    def get_node(self):
        return self._node

    def __str__(self):
        return self.__name


class StartVariable(Variable):
    def __init__(self, name, rule,options):
        Variable.__init__(self, name, None)
        self.__rule = rule
        self.__options = options

    def get_rule(self):
        return self.__rule

    def get_option(self, option):
        if option not in self.__options:
            return None
        return self.__options[option]

    def is_rule_valid(self, path):
        return re.match(self.__rule, path) is not None

    def set_node(self, node):
        self._node = node


class Relation:
    def __init__(self, name_a, name_b, operation, order=0, result_name=None):
        self.__name_a = name_a
        self.__name_b = name_b
        self.__operation = operation
        self.__order = order
        self.__result_name = result_name

    def __str__(self):
        string = self.__name_a + " " + self.__operation + " " + self.__name_b
        if self.__result_name is not None:
            string += " -> " + self.__result_name
        return string

    def is_valid_for_a(self, var):
        return self.__name_a == var.get_name()

    def is_valid_for_b(self, var):
        return self.__name_b == var.get_name()

    def process(self, var_a, var_b):
        # merge_node = nuke.createNode("Merge2") #TODO remove
        # merge_node["operation"].setValue(str(self.__operation))
        # merge_node.setInput(1, var_a.get_node())
        # merge_node.setInput(0, var_b.get_node())
        merge_node = nuke.nodes.Merge(operation=str(self.__operation), inputs=[var_b.get_node(), var_a.get_node()])
        if self.__result_name is None:
            return None
        return Variable(self.__result_name, merge_node)
