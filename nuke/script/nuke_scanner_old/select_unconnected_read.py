import nuke

def get_connected_nodes(node, collected=None):
    """
    Recursively get all nodes connected to the given node.
    """
    if collected is None:
        collected = set()

    if node is None or node in collected:
        return collected

    collected.add(node)

    # Check all the input nodes.
    for i in range(node.inputs()):
        input_node = node.input(i)
        if input_node is not None:
            get_connected_nodes(input_node, collected)

    # Check all the dependent nodes.
    for dependent in node.dependent():
        if dependent is not None:
            get_connected_nodes(dependent, collected)

    return collected


def run():
    """
    Select all Read nodes not connected to the currently selected node.
    """
    selected_nodes = nuke.selectedNodes()

    # Ensure a node is selected.
    if not selected_nodes:
        nuke.message("Please select a node.")
        return

    # Assuming a single node is selected for simplicity.
    selected_node = selected_nodes[0]

    # Get all nodes connected to the selected node.
    connected_nodes = get_connected_nodes(selected_node)

    # Deselect all nodes first.
    nuke.selectAll()
    nuke.invertSelection()

    # List to accumulate unused read nodes information.
    unused_reads = []

    # Loop through all Read nodes.
    for read_node in nuke.allNodes('Read'):
        if read_node not in connected_nodes:
            unused_info = "{} is not used: {}".format(read_node.name(), read_node.knob('file').value())
            unused_reads.append(unused_info)
            read_node.setSelected(True)

    # If there are any unused reads, display them in a popup.
    if unused_reads:
        message = "Total number of unused Read nodes: {}\n\n".format(len(unused_reads))
        message += "\n".join(unused_reads)
        nuke.message(message)
