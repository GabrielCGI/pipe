import pymel.core as pm
import maya.cmds as cmds

import json
import sys

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


def resetAttributes(nodeList, ud=True):
    transforms = {'translateX': 0.0,
                  'translateY': 0.0,
                  'translateZ': 0.0,
                  'rotateX': 0.0,
                  'rotateY': 0.0,
                  'rotateZ': 0.0,
                  'scaleX': 1.0,
                  'scaleY': 1.0,
                  'scaleZ': 1.0}

    for node in nodeList:
        resetDict = {}
        nodePath = node.fullPath()
        if node.hasAttr('resetAttr'):
            try:
                resetDict.update(json.loads(node.resetAttr.get().replace('\'', '"')))
            except:
                pass

        attributes = [at for at in transforms.keys()]
        if ud:
            udList = cmds.listAttr(nodePath, ud=True, keyable=True)
            if udList is None:
                udList = []
            attributes.extend(udList)
        attributes = [at for at in attributes if cmds.getAttr('{}.{}'.format(nodePath, at), settable=True)]

        for at in attributes:
            if at in resetDict:
                v = resetDict[at]
            elif at in transforms:
                v = transforms[at]
            else:
                v = cmds.attributeQuery(at, node=nodePath, listDefault=True)[0]

            cmds.setAttr('{}.{}'.format(nodePath, at), v)



