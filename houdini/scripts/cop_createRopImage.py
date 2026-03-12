import hou
def run():
    # 1. Get the currently selected node
    selected_nodes = hou.selectedNodes()

    if not selected_nodes:
        hou.ui.displayMessage("Please select a node first.")
    else:
        target_node = selected_nodes[0]
        parent_network = target_node.parent()
        node_name = target_node.name()
        
        # 2. Define the new name for the ROP node
        new_node_name = f"render_{node_name}"

        # 3. Create the ROP Image Output node
        rop_node = parent_network.createNode("rop_image", new_node_name)

        # 4. Set the 'coppath' parameter
        rop_node.parm("coppath").set(target_node.path())

        # 5. Set the 'copoutput' parameter (Output Picture)
        output_path = f"$HIP/comp/{node_name}.$F4.exr"
        rop_node.parm("copoutput").set(output_path)

        # 6. Set Precision to 16-bit
        # Enable the 'Set Precision' checkbox
        rop_node.parm("setprecision").set(1) 
   
        # 7. Position the node to the right
        pos = target_node.position()
        new_pos = hou.Vector2(pos[0] + 3.0, pos[1])
        rop_node.setPosition(new_pos)
        
        # 8. Select the new node and make it active
        rop_node.setSelected(True, clear_all_selected=True)
        
        print(f"Created {rop_node.name()} | Output: {output_path} | Precision: 16-bit")