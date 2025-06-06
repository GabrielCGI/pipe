import maya.api.OpenMaya as om
from maya import cmds


def getMDagPath(node_name):
    if node_name is None:
        return None

    if len(cmds.ls(node_name)) != 1:
        raise NameError('{} doesn\'t exists or is not unique'.format(node_name))

    sel = om.MSelectionList()
    sel.add(node_name)

    dag = sel.getDagPath(0)
    return dag


def getMObject(node_name):
    if node_name is None:
        return None

    if len(cmds.ls(node_name)) != 1:
        raise NameError('{} doesn\'t exists or is not unique'.format(node_name))

    sel = om.MSelectionList()
    sel.add(node_name)

    obj = sel.getDependNode(0)
    return obj


def getMFnDependencyNode(node_name):
    obj = getMObject(node_name)
    return om.MFnDependencyNode(obj)
