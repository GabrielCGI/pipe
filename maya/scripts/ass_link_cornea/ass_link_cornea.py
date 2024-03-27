import os
import sys
import re
import pymel.core as pm
import maya.cmds as cmds
from shiboken2 import wrapInstance

from common.utils import *
from .cornea_by_char import *


def __retrieve_datas(cornea_dict):
    """
    Retrieve the cornea for characters
    :param cornea_dict
    :return:
    """
    # Selection
    selection = pm.ls(selection=True)
    if len(selection) < 2:
        print_warning("Select atleast a light and an asset standin")
        return

    asset = selection[-1]
    try:
        shape = asset.getShape()
        if shape.type() != "aiStandIn": raise Exception()
    except:
        print_warning("The last element selected must be the asset standin")
        return

    asset_name = asset.name()
    match = re.match(r"^(?:(.*)_[0-9]{2}|(.*))$",asset_name)
    char_name = match.group(1) if match.group(1) is not None else match.group(2)
    if char_name not in cornea_dict:
        print_warning("The asset "+char_name+" hasn't been found in the project char list")
        cornea_shapes = None
    else:
        cornea_shapes = cornea_dict[match.group(1)]

    lights = pm.listRelatives(selection[:-1], fullPath=True)
    return shape, cornea_shapes, lights


def __light_link_cornea(shape, cornea_shapes, lights):
    """
    Light link the corneas
    :param shape
    :param cornea_shapes
    :param lights
    :return:
    """
    # Light Expression
    c = [l.fullPath().replace("|", "/") for l in lights]
    string = "' '".join(c)
    string = string.replace(",", "")
    light_expression = "['" + string + "']"
    # Corneas Expresion
    corneas_expression = "*" if cornea_shapes is None else "*"+ "* or *".join(cornea_shapes)+"*"
    # AiSetParameter
    ai_set_parameter = pm.createNode("aiSetParameter")
    # Light group
    pm.setAttr(ai_set_parameter + ".assignment[0]", "light_group=" + light_expression, type="string")
    pm.setAttr(ai_set_parameter + ".selection", corneas_expression, type="string")
    pm.setAttr(ai_set_parameter + ".assignment[1]", "bool use_light_group=True", type="string")
    # Shadow Group
    pm.setAttr(ai_set_parameter + ".assignment[2]", "shadow_group=" + light_expression, type="string")
    pm.setAttr(ai_set_parameter + ".selection", corneas_expression, type="string")
    pm.setAttr(ai_set_parameter + ".assignment[3]", "bool use_shadow_group=True", type="string")
    # Connect
    pm.connectAttr(ai_set_parameter+".out",shape+".operators[30]", f=True)



#def run():
#    """
#    Launch Asset link cornea
#    :return:
#    """
#    current_project_dir = os.getenv("CURRENT_PROJECT_DIR")
#    if current_project_dir is None:
#        print_warning("Current project dir not defined. Use an illogic launcher")
#    datas = __retrieve_datas(CORNEA_CHAR[current_project_dir])
#    if datas is None:
#        return
#    shape, cornea_shapes, lights = datas
#    __light_link_cornea(shape, cornea_shapes, lights)

def run():

    shape = pm.ls(sl=True)[-1].getShape()
    cornea_shapes= ""
    lights = pm.ls(sl=True, )[:-1]
    __light_link_cornea(shape, cornea_shapes, lights)
