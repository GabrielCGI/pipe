import maya.cmds as cmds
import os
from pymel.core import *


def scanAsset(obj):
    variants =[]
    asset = Asset(obj)
    vSets = [vSet for vSet in cmds.listRelatives(obj, fullPath=True) if short_name(vSet).startswith("variant_") ]

    if not vSets: warning("No variant set found")
    asset.vSets_list = vSets
    for vSet in vSets:
        variants += [Variant(var, vSet, obj) for var in cmds.listRelatives(vSet, fullPath=True)]
    if not variants:  warning("No variant found")

    proxy = get_from_asset(asset.name_long,asset.name+"_proxy", must_exist=False)
    logger.info('Scan success !')
    return asset, variants, proxy
