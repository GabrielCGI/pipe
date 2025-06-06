import pymel.core as pm
import maya.cmds as cmds
import json

def nextMultiAttributeIndex(attr):
    ids = attr.get(multiIndices=True)
    if ids is None:
        return 0
    else:
        return max(ids) + 1

def undoChunk(func):
    """
    Maya Undo decorator
    """
    def wrapper(*args, **kwargs):
        with pm.UndoChunk():
            return func(*args, **kwargs)
    return wrapper

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
