
"""
import sys
sys.path.append(r"D:\gabriel\_GITHUB\pipe\maya\scripts\assetizer_pymel")
import importlib as i
import API_ass
i.reload(API_ass)

API_ass.run()
"""

import sys
sys.path.append(r"R:\pipeline\networkInstall\arnold\Arnold-7.1.4.1-windows")
import pymel.core as pm
from arnold import *

class AssItem():
    def __init__(self, long_name, aiMatrix):
        self.long_name = long_name
        self.aiMatrix = aiMatrix
        self.matrix = aiMatrixToMaya(aiMatrix)
        self.short_name = long_name.split("/")[-1]

def aiMatrixToMaya(aiMatrix):
    m = []
    for i in range(0,4):
        for ii in range(0,4):
            m.append(aiMatrix[i][ii])
    return m

def scanAss(dso):
    items=[]
    AiBegin (AI_SESSION_BATCH )

    AiMsgSetConsoleFlags(AI_LOG_ALL)

    # Required if the ASS file uses any SItoA shaders
    #AiLoadPlugins('C:/softimage/workgroups/sitoa-3.4.0-2015/Addons/SItoA/Application/Plugins/bin/nt-x86-64')

    AiASSLoad(dso)
    # Iterate over all shader nodes
    iter = AiUniverseGetNodeIterator(AI_NODE_SHAPE)
    while not AiNodeIteratorFinished(iter):
        node = AiNodeIteratorGetNext(iter)
        node_name = AiNodeGetName( node )
        ne = AiNodeGetNodeEntry( node )

        if node_name and AiNodeIs( node, "polymesh" ):
            matrix = AiNodeGetMatrix( node, "matrix" )
            assItem = AssItem(node_name, matrix)

            items.append(assItem)
    AiNodeIteratorDestroy(iter)

    #AiEnd()
    return items




def createLocator(short_name,matrix):
    locator_shape = pm.createNode("locator",n=short_name)
    locator = locator_shape.getParent()
    pm.xform(locator,matrix=matrix)
    return locator

def createAiSetTransform(name, long_name):
    print(name)
    operator = pm.createNode("aiSetTransform", n="aiSetTransform_"+name)
    operator.selection.set(long_name)
    operator.mode.set(1)
    return operator

def connectOperator(locator, operator):
    pm.connectAttr(locator.translate, operator.translate)
    pm.connectAttr(locator.rotate, operator.rotate)
    pm.connectAttr(locator.scale, operator.scale)

def connectSetTransfromToAss(operator, ass, slot):
    pm.connectAttr(operator.out,ass.operators[str(slot)])

def getNextOperatorSlotAvailable(ass):
    counter = 0
    if pm.objectType(ass) == "aiStandIn":
        while True:
            counter +=1
            if len(pm.listConnections(ass.operators[str(counter)])) == 0:
                return counter
    else:
        pm.error("Not a standin ! %s"%ass)


def run(ass):
    dso = ass.dso.get()
    items = scanAss(dso)

    for i in items:

        print(i.short_name, i.long_name)
        locator= createLocator(i.short_name,i.matrix)
        operator = createAiSetTransform(i.short_name, i.long_name)
        slot = getNextOperatorSlotAvailable(ass)
        connectSetTransfromToAss(operator, ass, slot)
        connectOperator(locator,operator)
    print("succes !")
