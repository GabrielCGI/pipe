import sys
from USDToolBox_pck.updateAssetsUSD import assetitem
import hou

MODULE_PATH = "r:/pipeline/pipe/prism"
    
if not MODULE_PATH in sys.path:
    sys.path.insert(0, MODULE_PATH)

import USDToolBox_pck.updateAssetsUSD.usd_updater as usd_updater
import importlib
import cProfile
import pstats

PROFILER = cProfile.Profile()
PROFILER_DUMP = 'R:/pipeline/pipe/houdini/scripts/usdupdater/stats.prof'

PRISM_IMPORT_TYPE = 'prism::LOP_Import::1.0'
PRISM_BASE_COLOR = hou.Color(0.451, 0.369,0.796)
TO_UPDATE_COLOR = hou.Color(0.8, 0.1, 0.1)

def getPrismImport():
    stage = hou.node('/stage')
    prism_imports = []
    for node in stage.allNodes():
        if node.type().name() == PRISM_IMPORT_TYPE:
            prism_imports.append(node)
    return prism_imports
    

def checkEveryNodes():
    print('Start')
    PROFILER.clear()
    PROFILER.enable()

    from . import debug
    debug.debug()
    debug.debugpy.breakpoint()

    selected_nodes = hou.selectedNodes()
    hou.clearAllSelected()

    prism_imports = getPrismImport()    
    for node in prism_imports:
        
        path = node.parm('filepath').eval()
        instance = hou.qt.mainWindow()
        updater = usd_updater.MainInterface(
            openType='houdini',
            pathPrism=path,
            ar_context=None,
            parent=instance
        )
        
        layers = updater._layers
        
        is_update = True
        for layer in layers:
            if updater._assetsToUpdate.get(layer.identifier):
                is_update = False
                break
        
        if is_update:
            node.setColor(PRISM_BASE_COLOR)
            print(f"{node.name()} is updated")
        else:
            node.setColor(TO_UPDATE_COLOR)
            print(f"{node.name()} need to be updated")

    if selected_nodes:
        for node in selected_nodes:
            node.setSelected(True)
    
    PROFILER.disable()        
    print('End')
    stats = pstats.Stats(PROFILER)
    stats.strip_dirs().sort_stats('cumtime').dump_stats(PROFILER_DUMP)
