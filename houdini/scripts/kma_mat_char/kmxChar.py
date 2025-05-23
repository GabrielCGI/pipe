"""
Houdini Material Manager
A utility script for creating and managing materials in Houdini's USD workflow.

This script helps with:
1. Creating Karma material builders from USD materials
2. Managing material collections
3. Assigning materials to geometry components

Author: Valentin ValDo Dornel
Credits: Gabriel Grapperon
License: MIT License 2024
Version: 1.0
Status: Production
"""

import hou
import voptoolutils
import colorsys
import re
import sys
from pxr import UsdShade

# Debug settings
PRINT_DEBUG = False
PRINT_INFO = True


def print_info(message):
    """Print informational messages if info printing is enabled."""
    if PRINT_INFO:
        print(f"INFO - {message}")


def print_debug(message):
    """Print debug messages if debug printing is enabled."""
    if PRINT_DEBUG:
        print(f"DEBUG - {message}")


def clean_string(text):
    """
    Convert a string to a valid Houdini node name by replacing invalid characters.
    
    Args:
        text (str): Original string that may contain invalid characters
        
    Returns:
        str: Cleaned string suitable for Houdini node names
    """
    return re.sub(r'[^A-Za-z0-9_-]', '_', text)


def set_network_view_path(node):
    """
    Change the current path of the Network View in Houdini.

    Args:
        node (hou.Node): The node whose context should be displayed in Network View
    """
    try:
        # Get the current network editor
        network_editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)

        if network_editor is None:
            raise ValueError("No network view found.")

        # Change the network editor's current path
        network_editor.setPwd(node)

    except Exception as e:
        print(f"Error setting network view path: {e}")


def change_material_path(material_library):
    """
    Update the material path prefix based on the 'mtl' prim in the USD stage.
    
    Args:
        material_library (hou.Node): The material library node containing the USD stage
    
    Raises:
        RuntimeError: If no 'mtl' prim is found in the stage
    """
    print_debug("Changing material path")
    stage = material_library.stage()
    
    # Search for a prim named 'mtl'
    mtl_prim = None
    for prim in stage.Traverse():
        if prim.GetName() == "mtl":
            mtl_prim = prim
            break
            
    # If found, update the parameter
    if mtl_prim:
        path = mtl_prim.GetPath().pathString
        if not path.endswith("/"):
            path += "/"
        material_library.parm("matpathprefix").set(path)
    else:
        raise RuntimeError("No prim named 'mtl' found in the stage.")


def get_materials(node):
    """
    Retrieve materials from a USD stage.
    
    Args:
        node (hou.Node): Node containing the USD stage to search
        
    Returns:
        dict: Dictionary mapping material paths to their child names
        
    Raises:
        RuntimeError: If unable to get the USD stage from the node
    """
    stage = node.stage()
    if not stage:
        hou.ui.displayMessage("Failed to get USD stage from node.", severity=hou.severityType.Error)
        raise RuntimeError("Failed to get USD stage from node.")
        
    materials_dict = {}

    for prim in stage.Traverse():
        if UsdShade.Material(prim):
            material_path = str(prim.GetPath())
            child_names = [child.GetName() for child in prim.GetChildren()]
            materials_dict[material_path] = child_names

    return materials_dict


def check_selection():
    """
    Verify that the user has selected a material library node.

    Returns:
        hou.Node: The selected material library node
        
    Raises:
        SystemExit: If the selection is invalid
    """
    selection = hou.selectedNodes()
    if len(selection) >= 1:
        material_library = None

        for node in selection:
            if node.type().name() == "materiallibrary":
                material_library = node

        if material_library is not None:
            return material_library
        else:
            hou.ui.displayMessage("Error while finding nodes, check your selection")
            sys.exit()
    else:
        hou.ui.displayMessage("You need to select a materiallibrary")
        sys.exit()


def create_karma_mat_builder(material_library_node, mtl_name, standard_surface_name):
    """
    Create a Karma Material Builder node inside the material library.
    
    This function uses viewport interaction to create the node in the correct context.
    
    Args:
        material_library_node (hou.Node): The material library node where the builder will be created
        mtl_name (str): Name for the Karma Material Builder node
        standard_surface_name (str): Name for the standard surface node inside the builder
        
    Returns:
        hou.Node: The created Karma Material Builder node
    """
    print_debug("Creating Karma Material Builder")
    set_network_view_path(material_library_node)

    mask = voptoolutils.KARMAMTLX_TAB_MASK

    viewer = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)

    kwargs = {
        "pane": viewer,
        "autoplace": True
    }

    voptoolutils.createMaskedMtlXSubnet(kwargs, "karmamaterial", mask, "Karma Material Builder", "kma")
    karma_subnet_node = hou.selectedNodes()[0]
    print_debug(f"Material name: {mtl_name}, Surface name: {standard_surface_name}")
    karma_subnet_node.setName(mtl_name, unique_name=True)

    # Find and rename the mtlxstandard_surface node inside the subnet
    for child in karma_subnet_node.children():
        if child.type().name() == "mtlxstandard_surface":
            child.setName(standard_surface_name, unique_name=True)
            break

    print_debug(f"Created node: {karma_subnet_node}")
    return karma_subnet_node


def randomize_base_color(kmb_node, step, divider):
    """
    Set the base color of a material using the HSV color model to create visually distinct colors.
    
    Args:
        kmb_node (hou.Node): The Karma Material Builder node
        step (int): Current index in the sequence of materials
        divider (int): Total number of materials for color distribution
        
    Returns:
        tuple: (r, g, b) color values
    """
    try:
        # Find the mtlxstandard_surface node
        mtlx_node = None
        for child in kmb_node.children():
            if child.type().name() == "mtlxstandard_surface":
                mtlx_node = child
                break

        if mtlx_node is None:
            raise ValueError("No 'mtlxstandard_surface' node found in the Karma Material Builder.")

        # Calculate color based on position in sequence
        h = float(step) / float(divider)
        r, g, b = colorsys.hsv_to_rgb(h, 0.6, 0.9)

        # Update 'base_color' on the shader
        mtlx_node.parmTuple('base_color').set((r, g, b))

        return r, g, b

    except Exception as e:
        print(f"Error setting material color: {e}")


def create_karma_materials(materials_dict, material_library):
    """
    Create Karma Material nodes for each material in the dictionary.
    
    Args:
        materials_dict (dict): Dictionary of material paths and their child names
        material_library (hou.Node): The material library node where materials will be created
        
    Returns:
        list: List of material paths that were created
    """
    network_editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    lop_network = network_editor.pwd()

    # Get existing children names in the material library
    existing_children = {child.name() for child in material_library.children()}

    # Iterate over materials in the dictionary
    for i, (mtl_path, child_list) in enumerate(materials_dict.items()):
        short_mtl_name = mtl_path.split('/')[-1]
        if short_mtl_name not in existing_children:
            # Use the first child name as the standard surface name, or provide a fallback
            standard_surface_name = child_list[0] if child_list else "standard_surface"

            # Create the Karma Material Builder
            kma_subnet = create_karma_mat_builder(material_library, short_mtl_name, standard_surface_name)

            # Set color based on index
            rand_color = randomize_base_color(kma_subnet, i, len(materials_dict))
            kma_subnet.setColor(hou.Color(rand_color))
        else:
            print_info(f"Material name {short_mtl_name} already exists in {material_library}, skipping")

    network_editor.setPwd(lop_network)
    return list(materials_dict.keys())


def execute():
    """
    Main execution function that processes material libraries and creates Karma materials.
    """
    # Check selection and get material library node
    material_library = check_selection()
    print_debug(material_library)

    # Get materials from the library and update the material path
    materials_dict = get_materials(material_library)
    change_material_path(material_library)
    
    # Save the current update mode and set to manual for better performance
    mode = hou.updateModeSetting()
    hou.setUpdateMode(hou.updateMode.Manual) 
    
    # Create the materials
    mtl_list = create_karma_materials(materials_dict, material_library)
    how_many_mtl = len(mtl_list)
    print_debug(f"Total materials: {how_many_mtl}")
    
    # Confirm with user if there are many materials to create
    if how_many_mtl > 20:
        cancel_ui = hou.ui.displayMessage(
            f"There are {how_many_mtl} materials to create, it will take some time. Continue?", 
            severity=hou.severityType.ImportantMessage, 
            buttons=('Sure, let\'s go!', 'Cancel')
        )
        if cancel_ui != 0:
            # Restore update mode and exit
            hou.setUpdateMode(mode)
            return
    
    # Restore update mode
    hou.setUpdateMode(mode)


if __name__ == "__main__":
    print_debug("\n\n-- New Execution --\n\n")
    execute()