from maya import cmds
import pymel.core as pm
import json
import sys
from gf_animtools.utilities import maya_api


def mirrorCtr():
    newValues = {}
    for obj in pm.ls(sl=True):
        if not obj.hasAttr('mirrorData'):
            continue

        mirObj = obj.mirObj.get()
        mirValues = json.loads(obj.mirValues.get())

        keyables = pm.listAttr(obj, k=True, sn=True)
        keyables = [k for k in keyables if k in mirValues]
        new = {}
        for k in keyables:
            if mirObj is not None:
                if mirObj.hasAttr(k):
                    new[k] = mirObj.attr(k).get() * mirValues[k]
            else:
                new[k] = obj.attr(k).get() * mirValues[k]
        newValues[obj] = new

    for obj, values in newValues.items():
        for at, v in values.items():
            at = obj.attr(at)
            try:
                at.set(v)
            except:
                sys.stderr.write('{} : Couldn\'t set value {} on {}'.format(obj, v, at))


def setDynamicValue(value):
    for node_name in cmds.ls(type='transform', long=True):
        fn = maya_api.getMFnDependencyNode(node_name)
        if fn.hasAttribute('dynamic'):
            cmds.setAttr('{}.dynamic'.format(node_name), value)


