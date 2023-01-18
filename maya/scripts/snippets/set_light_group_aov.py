

import pymel.core as pm

aov_name = "lightA"
# Get current selection
current_selection = pm.ls(selection=True)

# Iterate over the selection
for obj in current_selection:
    # Get shape node
    shape_node = obj.getShape()
    # Check if the attribute exists
    if pm.attributeQuery('aiAov', node=shape_node, exists=True):
        # Set the attribute to "default"
        pm.setAttr(shape_node + '.aiAov', aov_name, type='string')
    else:
        print(f"attribute .aiAov does not exist on object {obj}")