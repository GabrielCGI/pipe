import math
import sys


def unload_packages(silent=True, package=None):
    if package is None:
        return
    # construct reload list
    reload_list = []
    for i in sys.modules.keys():
        if i.startswith(package):
            reload_list.append(i)
    # unload everything
    for i in reload_list:
        try:
            if sys.modules[i] is not None:
                del (sys.modules[i])
                if not silent:
                    print("Unloaded: %s" % i)
        except:
            pass


def __get_val(v):
    if type(v) is str:
        return "\"" + v + "\""
    else:
        return str(v)


def print_var(*vs):
    vs = vs[0] if len(vs) == 1 else vs
    tabulation = "`\t"
    print(__print_var_aux(vs, tabulation))


def __print_var_aux(v, tabulation, tabs=0, v_in_dict=False):
    str_msg = ""
    if type(v) is dict:
        if len(v) == 0:
            str_msg += "{}\n"
        else:
            if v_in_dict:
                str_msg += "\n"
            str_msg += tabs * tabulation + "{\n"
            for key, elems in v.items():
                str_msg += (tabs + 1) * tabulation + __get_val(key) + " : "
                str_msg += __print_var_aux(elems, tabulation, tabs + 1, True)
            str_msg += tabs * tabulation + "}\n"
    elif type(v) is list or type(v) is tuple:
        if type(v) is list:
            char_start = "["
            char_end = "]"
        else:
            char_start = "("
            char_end = ")"
        if len(v) == 0:
            str_msg += char_start + char_end + "\n"
        else:
            if v_in_dict:
                str_msg += "\n"
            str_msg += tabs * tabulation + char_start + "\n"
            for elem_list in v:
                str_msg += __print_var_aux(elem_list, tabulation, tabs + 1, False)
            str_msg += tabs * tabulation + char_end + "\n"
    else:
        tabs_str = "" if v_in_dict else tabs * tabulation
        try:
            str_msg += tabs_str + __get_val(v) + "\n"
        except:
            str_msg += tabs_str + "Unknown value" + "\n"
    return str_msg
