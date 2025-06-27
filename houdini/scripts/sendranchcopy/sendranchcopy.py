import os
import hou
import PrismInit
import threading

RANCH_EXPORTER_PATH = "R:/pipeline/pipe/prism/ranch_cache_scripts"
import sys
sys.path.append(RANCH_EXPORTER_PATH)

LOP_FILECACHE = PrismInit.pcore.getPlugin('USD').api.usdExport
import ranchExporter

def run(dev=False):
    
    selected_nodes = hou.selectedNodes()
    
    if not selected_nodes:
        hou.ui.displayMessage(
            text='Please select 1 node in the network view.',
            severity=hou.severityType.Warning)
        return
    
    selected_node = selected_nodes[0]
    
    try:
        state = LOP_FILECACHE.getStateFromNode({'node': selected_node}).ui
    except Exception as e:
        hou.ui.displayMessage(
            text=(
                'Could not retrieve state from selected '
                'node, please select a LOP Filecache'
            ),
            severity=hou.severityType.Warning,
            details=e)
        return
    
    scenefile = hou.hipFile.name()
    kwargs = {'state': state, 'scenefile': scenefile}
    name = os.path.basename(hou.hipFile.name())
    
    if not name:
        hou.ui.displayMessage(
            text='Could not retrieve USD stage from selected node.',
            severity=hou.severityType.Warning)
        return
    
    if dev:
        print('Start parse and copy in dev mode')
        ranchExporter.parseAndCopyToRanchDev(name, kwargs)
    else:
        print('Start parse and copy in main mode')
        startCopy(name, kwargs)
    
    
def startCopy(stage, scene_path):
    thread = threading.Thread(target=ranchExporter.parseAndCopyToRanch, args=(stage, scene_path))
    thread.start()
