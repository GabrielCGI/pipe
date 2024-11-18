import nuke

def render_all_writes():
    # Get all Write nodes in the script
    write_nodes = [node for node in nuke.allNodes('Write')]
    
    # Render each Write node
    for write_node in write_nodes:
        try:
            # Get the last frame value and ensure it's an integer
            last_frame = int(write_node['last'].value())
            # Render the Write node
            nuke.execute(write_node.name(), 1, last_frame)
            print("Rendered: {}".format(write_node.name()))
        except Exception as e:
            print("Failed to render {}: {}".format(write_node.name(), e))

# Call the function
render_all_writes()
