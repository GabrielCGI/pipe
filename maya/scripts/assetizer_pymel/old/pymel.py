import maya.cmds as cmds
import os
import pymel.core as pm


    
asset = pm.ls(sl=True)[0]
def warning(txt):
    #pm.confirmDialog(message= txt)
    pm.error(txt)

def nameOnly(obj):
    nameOnly = obj.name().split("|")[-1]
    return nameOnly
print("yo")    
def scanAsset(asset):
    asset = pm.ls(sl=True)[0]
    variants=[]
    vSets = [vSet for vSet in pm.listRelatives(asset) if nameOnly(vSet).startswith("variant") ]

    if not vSets: warning("No variant set found")
    for vSet in vSets:
        variants += [var for var in pm.listRelatives(vSet)]
    if not variants:  warning("No variant found")

    return asset, variants, 

scanAsset(asset)