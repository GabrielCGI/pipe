from common.utils import *


class MergeMode:
    def __init__(self, relations):
        self.__var_set = None
        self.__relations = relations

    def set_var_set(self, var_set):
        self.__var_set = var_set

    def get_relations(self):
        return self.__relations

    def run(self):
        if self.__var_set is None:
            return
        for rel_order_data in self.__relations:
            vars_used = []
            vars_created = []
            for rel in rel_order_data:
                vars_a = []
                vars_b = []
                active_vars = self.__var_set.get_active_vars()
                for var in active_vars:
                    if rel.is_valid_for_a(var):
                        vars_a.append(var)
                    elif rel.is_valid_for_b(var):
                        vars_b.append(var)
                if len(vars_a) == 0 or len(vars_b) == 0:
                    continue
                for var_a in vars_a:
                    for var_b in vars_b:
                        result_var = rel.process(var_a, var_b)
                        if result_var is not None:
                            vars_created.append(result_var)
                vars_used.extend(vars_a)
                vars_used.extend(vars_b)
            for var_used in vars_used:
                self.__var_set.active_var(var_used, False)
            for var_created in vars_created:
                self.__var_set.active_var(var_created, True)