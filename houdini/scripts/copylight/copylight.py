import hou

LIGHT_MAKER_TYPE = 'illogic::Light_maker_2::1.1'
OLD_SUFFIX = '_old'

def copySelectedLights():
    """
    Copy all light maker selected into a light maker HDA.
    """    

    lights_to_copy: hou.Node = hou.selectedNodes()
    
    # Check if a light node is selected
    if len(lights_to_copy) == 0:
        hou.ui.displayMessage("Please select a node",
                              severity=hou.severityType.Message)

    for light in lights_to_copy:
        copyLight(light)
    

def copyLight(light_to_copy: hou.Node):
    """Copy a light maker subnetwork into the brand new
    light maker HDA.

    Args:
        light_to_copy (hou.Node): Light maker subnetwork to copy
    """

    # Copy the name and add a '_old' suffix to the copied light
    light_name = light_to_copy.name()
    if (light_name.endswith(OLD_SUFFIX)):
        light_name = light_name.removesuffix(OLD_SUFFIX)
    light_to_copy.setName(f"{light_name}{OLD_SUFFIX}")

    # Create the new HDA node with the same name in the same network
    light_parent = light_to_copy.parent()
    light_to_paste: hou.Node = light_parent.createNode(
        LIGHT_MAKER_TYPE, light_name)

    # Position the node close to the old one
    light_position = light_to_copy.position()
    light_to_paste.setPosition(light_position)

    offset = hou.Vector2(-3, 0)
    light_to_copy.setPosition(offset + light_position)

    # Copy each parameters in the new node
    for parm in light_to_copy.parms():

        # Check if the parameters exists in the HDA
        parm_names_list = [p.name() for p in light_to_paste.parms()]
        if parm.name() in parm_names_list:

            parm_to_paste = light_to_paste.parm(parm.name())
            parm_to_copy = light_to_copy.parm(parm.name())

            parm_to_paste.set(parm_to_copy.eval())

    ## Copy each connections in the new node
    # Input connections :
    for connection in light_to_copy.inputConnections():
        input_node = connection.inputNode()
        # Input index of light_to_copy
        input_index = connection.inputIndex()
        # Output index of input_node
        output_index = connection.outputIndex()
        
        # Copy then remove connection
        light_to_paste.setInput(input_index, input_node, output_index)
        light_to_copy.setInput(input_index, None)

    # Output connections :
    for connection in light_to_copy.outputConnections():
        output_node = connection.outputNode()
        # Input index of light_to_copy
        input_index = connection.inputIndex()
        # Output index of input_node
        output_index = connection.outputIndex()
        
        # Copy then remove connection
        output_node.setInput(input_index, None)
        output_node.setInput(input_index, light_to_paste, output_index)