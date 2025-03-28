import hou
import threading

from . import ranchExporter

def run():
    
    selected_nodes = hou.selectedNodes()
    
    if not selected_nodes:
        hou.ui.displayMessage(
            text='Please select 1 node in the network view.',
            severity=hou.severityType.Warning)
        return
    
    selected_node = selected_nodes[0]
    
    stage = selected_node.stage()
    
    if not stage:
        hou.ui.displayMessage(
            text='Could not retrieve USD stage from selected node.',
            severity=hou.severityType.Warning)
        return
        
    scene_path = hou.hipFile.path()
    
    startCopy(stage, scene_path)
    
    
def startCopy(stage, scene_path):
    thread = threading.Thread(target=ranchExporter.parseAndCopyToRanch, args=(stage, scene_path))
    thread.start()
