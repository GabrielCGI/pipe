import nuke

def run():
    try:
        # Verify that a node is selected and is a Cryptomatte node
        selected_node = nuke.selectedNode()
        assert selected_node.Class() == 'Cryptomatte', "Selected node is not a Cryptomatte."

        # Ask the user for the mask name
        mask_name = nuke.getInput("Enter mask name", "")
        if not mask_name:  # Check if the user pressed cancel or entered an empty string
            nuke.message("No mask name provided.")
            return

        # Create a PostageStamp node
        postage_stamp_node = nuke.createNode('PostageStamp')
        
        # Set the knobs for the PostageStamp node
        postage_stamp_node['hide_input'].setValue(True)
        postage_stamp_node['postage_stamp'].setValue(False)

        # Rename and align PostageStamp node
        postage_stamp_node.setName(mask_name + "_Stamp")
        postage_stamp_node.setXpos(selected_node.xpos())
        postage_stamp_node.setYpos(selected_node.ypos() + 50)

    except (ValueError, AssertionError, Exception) as e:
        nuke.message(str(e))