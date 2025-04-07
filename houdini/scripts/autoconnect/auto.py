import os
import glob
import re

import hou
import voptoolutils

import autoconnect.maps as maps
import autoconnect.ressource as ressource
import autoconnect.houdinilog as hlog


def log_shaders(shaders):
    space = " "*3
    for sh in shaders:
        hlog.pdebug(sh.name)
        for map in sh.maps:
            hlog.pdebug(space + map.path)
            hlog.pdebug(space + map.maps_type)
            hlog.pdebug(space + map.data_type)

def get_shaders_from_dir(directory_path):
    """
    Get each shaders from maps in a directory and his sub directories.

    Format: ***_version_name_map-type_signature(_.udim)_(.extension)

    Args:
    directory_path (str): path to directory containing maps

    Return:
    list: list of Shader
    """

    directory_path = os.path.join(directory_path, "**")

    shaders = []
    for file in glob.glob(pathname=directory_path, recursive=True):
        extension = os.path.splitext(file)[1]
        if extension in ressource.EXTENSION:
            directory_path, file_name = os.path.split(file)

            version_match = re.search("v\d{4}", file_name)

            # Check if the name has a version flag
            if version_match is None:
                continue

            version_span = version_match.span()
            first_key_span = maps.firstKeyWord(file_name)
            if first_key_span is not None:
                shader_name =  file_name[
                    version_span[1]+1:
                    first_key_span[0]-1]

                found = False
                for shader in shaders:
                    if shader.name == shader_name:
                        shader.parse(file)
                        found = True

                if not found:
                    newShader = maps.Shader(shader_name)
                    newShader.parse(file)
                    shaders.append(newShader)
    return shaders

def set_node_connection(input_node, output_node, input_name, output_name):
    """
    Set a connection between two nodes.

    Args:
    input_node (hou.VopNode): Node that receive the connection
    output_node (hou.VopNode): Node that send the connection
    input_name (str): Input's label of the output_node
    output_name (str): Output's label of the input_node
    """

    input_index = output_node.inputIndex(input_name)
    output_index = input_node.outputIndex(output_name)

    # Check index validity
    if (input_index < 0 or output_index < 0):
        hlog.pinfo(f"Could not connect ({input_node.name()})"
                   + f" to ({output_node.name()})")
        if input_index < 0:
            hlog.pdebug(f"Cannot find ({input_name})"
                        + f" index in ({output_node.name()})")
        if output_index < 0:
            hlog.pdebug(f"Cannot find ({output_name})"
                        + f" index in ({input_node.name()})")
        return

    # Set the connection as an input to the output node
    output_node.setInput(input_index, input_node, output_index)

def plug_shader(shader, material_library):
    """
    Plug maps from a shader in a subnetwork of material_library.

    Create a subnetwork of material_library, if a subnetwork
    with the shader's name exists, rename the old one as
    "(shader's name)_old". Then bind each maps of the shader to the
    corresponding node.

    Args:
    shader (maps.Shader): Shader to build
    material_library (hou.Node)
    """

    # Check existing subnetwork
    material_library_subnetworks = material_library.children()

    for subnet in material_library_subnetworks:
        if shader.name in subnet.name():
            if not re.search("_old", subnet.name()):
                subnet.setName(subnet.name() + "_old")

    # Create a new subnetwork for the shader
    mask = voptoolutils.KARMAMTLX_TAB_MASK
    viewer = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    kwargs = {
        "pane":viewer,
        "autoplace":True
    }

    current_subnet = voptoolutils.createMaskedMtlXSubnet(kwargs,
                                        shader.name,
                                        mask,
                                        "Karma Material Builder",
                                        "kma")

    # Create and set each maps
    surface = None
    displacement = None
    for node in current_subnet.children():
        if node.type().name() == 'mtlxstandard_surface':
            surface = node
        if node.type().name() == 'mtlxdisplacement':
            displacement = node


    if not surface:
        hlog.pdebug("Surface not generated.")
        hou.ui.displayMessage("Surface not generated.")
        return

    for map in shader.maps:
        node_map = current_subnet.createNode(node_type_name='mtlximage',
                                             node_name=map.name)
        node_map.parm('signature').set(map.signature)
        node_map.parm('file').set(map.path)
        # hlog.pdebug(map.path)

        # Plug each map
        out_index = node_map.outputIndex('out')
        in_label = 'in'
        out_label = 'out'

        # WIP
        # hlog.pdebug(out_index)
        if map.maps_type == 'normal':
            # continue
            node_map.parm('signature').set('vector3')
            normal_map = current_subnet.createNode('mtlxnormalmap')
            set_node_connection(node_map,
                                normal_map,
                                in_label,
                                out_label)
            set_node_connection(normal_map,
                                surface,
                                map.maps_type,
                                out_label)
        elif map.maps_type == "Height":
            # continue #WIP
            displacement_label = 'displacement'
            set_node_connection(node_map,
                                displacement,
                                displacement_label,
                                out_label)
        else:
            set_node_connection(node_map,
                                surface,
                                map.maps_type,
                                out_label)

    current_subnet.layoutChildren()

def ask_confirmation(shaders) -> bool:
    if not shaders:
        hlog.pinfo("No shaders found.")
        hou.ui.displayMessage("No shaders found.")
        return False
    else:
        hlog.pdebug(str(len(shaders)) + " shaders found.")

    shaders_infos = ""

    for shader in shaders:
        shaders_infos += f"{shader.name}\n"

    confirmation_message = ("The following shaders will be created:\n\n" + shaders_infos)
    user_choice = hou.ui.displayMessage(
        confirmation_message, buttons=('Confirm', 'Cancel'),
        default_choice=0, close_choice=1)

    if user_choice == 0:
        hlog.pinfo(f"Building shaders...")
        return True
    else:
        hlog.pinfo("Update cancelled by the user.")
        return False


def run():

    ressource.load()

    # Start directoy will be current working directory
    start_directory = os.getcwd()

    # Check if the material library node is selected
    material_library = hou.selectedNodes()
    if (not material_library
        or material_library[0].type().name() != 'materiallibrary'):
        hlog.pinfo("Material library node is not selected.")
        hou.ui.displayMessage("Material library node is not selected.")
        return
    else:
        material_library = material_library[0]
        hlog.pdebug("Material library node is selected.")

    # Check if the network panel is an active panel
    netpane = None
    for pane in hou.ui.paneTabs():
        if pane.type() == hou.paneTabType.NetworkEditor:
            netpane = pane
            break

    if netpane is None:
        hlog.pdebug("Network panel is not active.")
        hou.ui.displayMessage("Network panel is not active.")
        return
    else:
        netpane.setPwd(material_library)

    # Ask user where to parse maps
    dir_path = hou.ui.selectFile(file_type=hou.fileType.Directory,
                                 start_directory=start_directory)

    # Check if the path lead to a directory
    if not os.path.isdir(dir_path):
        hlog.pinfo("No directory selected.")
        hou.ui.displayMessage("No directory selected.")
        return
    else:
        hlog.pdebug(dir_path)


    # Parse map and output them to a list of Shader
    shaders = get_shaders_from_dir(dir_path)

    # Confirm updates with the user
    if not ask_confirmation(shaders):
        return

    for shader in shaders:
        plug_shader(shader, material_library)

    hlog.pinfo("Shaders built.")

    # log_shaders(shaders)
    return
