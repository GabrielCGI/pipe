import re
import nuke
from common.utils import *


class VariablesSet:
    def __init__(self, rule_vars):
        """
        Constructor
        :param rule_vars
        """
        self.__start_vars = rule_vars
        self.__active_vars = []

    def get_start_vars(self):
        """
        Getter of the start variables
        :return: start variables
        """
        return self.__start_vars

    def get_active_vars(self):
        """
        Getter of the active variables
        :return: active variables
        """
        return self.__active_vars

    def get_start_variable_valid_for(self, layer_name):
        """
        Getter of the first start variable valid for a specific layer name
        :param layer_name
        :return: start variable
        """
        for start_var in self.__start_vars:
            if start_var.is_rule_valid(layer_name):
                return start_var
        return None

    def active_var(self, var, active=True):
        """
        Set a variable to active or inactive
        :param var
        :param active
        :return:
        """
        if active:
            self.__active_vars.append(var)
        else:
            self.__active_vars.remove(var)


class Variable:
    def __init__(self, name, node, aliases=None, step=0):
        """
        Constructor
        :param name
        :param node
        :param aliases
        :param step
        """
        self.__name = name
        self._node = node
        self.__aliases = [] if aliases is None else aliases
        self.__step = step

    def get_name(self):
        """
        Getter of the name of the variable
        :return: name
        """
        return self.__name

    def get_node(self):
        """
        Getter of the node of the variable
        :return: node
        """
        return self._node

    def get_aliases(self):
        """
        Getter of the aliases of the variable
        :return: aliases
        """
        return self.__aliases

    def get_step(self):
        """
        Getter of the step of the variable (needed when the merge section is running to know the layout order)
        :return: step
        """
        return self.__step

    def set_node(self, node):
        """
        Setter of the node of the variable
        :param node
        :return:
        """
        self._node = node

    def __str__(self):
        """
        To String method
        :return: name
        """
        return self.__name


class StartVariable(Variable):

    @staticmethod
    def copy(start_var):
        """
        Copy method
        :param start_var
        :return: copy of start_var
        """
        return StartVariable(
            start_var.get_name(),
            start_var.__layer,
            start_var.__rule,
            start_var.get_aliases(),
            start_var.__order,
            start_var.__options,
            start_var.__group_operation
        )

    def __init__(self, name, layer, rule="", aliases=None, order=0, options=None, group_operation="over"):
        """
        Constructor
        :param name
        :param layer
        :param rule
        :param aliases
        :param order
        :param options
        :param group_operation
        """
        Variable.__init__(self, name, None, aliases)
        self.__rule = rule
        self.__layer = layer
        self.__order = order
        self.__options = {} if options is None else options
        self.__group_operation = group_operation

    def get_group_operation(self):
        """
        Getter of the group_operation of the start variable
        :return: group operation
        """
        return self.__group_operation

    def get_order(self):
        """
        Getter of the order of the start variable
        :return: order
        """
        return self.__order

    def get_layer(self):
        """
        Getter of the layer of the start variable
        :return: layer
        """
        return self.__layer

    def set_layer(self, layer):
        """
        Setter of the layer of the start variable
        :param layer
        :return:
        """
        self.__layer = layer

    def get_option(self, option_key):
        """
        Getter of the option of the start variable
        :param option_key
        :return: option
        """
        if option_key not in self.__options:
            return None
        return self.__options[option_key]

    def is_rule_valid(self, layer_name):
        """
        Check of a layer name is valid for the starrt variable
        :param layer_name
        :return: is rule valid
        """
        return re.match(self.__rule, layer_name) is not None
