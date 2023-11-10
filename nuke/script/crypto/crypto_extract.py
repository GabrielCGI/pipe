import nuke

def run():
    try:
        # Verify that a node is selected and is a Cryptomatte node
        selected_node = nuke.selectedNode()
        assert selected_node.Class() == 'Cryptomatte', "Selected node is not a Cryptomatte."
        assert 'decryptomatte' in selected_node.knobs(), "No decryptomatte knob found."

        # Ask the user for the mask name
        mask_name = nuke.getInput("Enter mask name", "")
        if not mask_name:  # Check if the user pressed cancel or entered an empty string
            nuke.message("No mask name provided.")
            return

        # Store the names of all nodes before decryption
        nodes_before = set(n.name() for n in nuke.allNodes())
        selected_node['decryptomatte'].execute()

        # Find the new node created by comparing the current node set to the previous
        nodes_after = set(n.name() for n in nuke.allNodes())
        new_nodes = nodes_after - nodes_before

        if new_nodes:
            new_node_name = new_nodes.pop()
            new_node = nuke.toNode(new_node_name)
            selected_node['selected'].setValue(False)
            new_node['selected'].setValue(True)
            
            # Rename the new node
            new_node.setName(mask_name)

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