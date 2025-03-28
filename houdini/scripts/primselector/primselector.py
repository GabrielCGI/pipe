
import hou
from pxr import Sdf

def run():
    nodes = hou.selectedNodes()
    if not nodes:
        hou.ui.displayMessage(
            text='Please select 1 node in the network view',
            severity=hou.severityType.Warning)
        return
    
    node:hou.LopNode = nodes[0]
    network:hou.LopNetwork = node.network()
    
    try:
        stage = node.stage()
    except Exception as e:
        hou.ui.displayMessage(
            text=f"Could not open stage from ({node})",
            details=f":\n {e}",
            severity=hou.severityType.Warning)
        return
    
    pattern = '**'
    rule = hou.LopSelectionRule()
    rule.setTraversalDemands(hou.lopTraversalDemands.NoDemands)
    rule.setPathPattern(pattern)

    prim_path = rule.expandedPaths(stage=stage)

    _, attributes_inputs = hou.ui.readMultiInput(
        message=('Please enter an attribute name and value.\n'),
        input_labels=('Attribute Name', 'Attribute Value'))
    attribute_name = attributes_inputs[0]
    value_wanted = attributes_inputs[1]

    prim_to_select = []
    for path in prim_path:
        attr_path = f'{path}.{attribute_name}'
        attr = stage.GetAttributeAtPath(attr_path)
        if not attr.IsValid():
            continue
        
        try:
            value = attr.Get()
        except Exception as e:
            print(f'Could not get value:\n {e}')
            return
        
        if value == value_wanted:
            prim_to_select.append(str(path))

    print(f'Selected {len(prim_to_select)} prims')
    network.setSelection(prim_to_select)