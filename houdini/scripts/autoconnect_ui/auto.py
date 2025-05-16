import os
import glob
import re
import colorsys

import hou
import voptoolutils

from . import map as mp
from . import shader as sh
from . import ressource as ressource
from . import houdinilog as hlog

def log_shaders(shaders):
    """Simple function to log shaders

    Args:
        shaders (list[sh.Shader]): List of shaders
    """    
    space = " "*3
    for sh in shaders:
        hlog.pdebug(sh.name)
        for map in sh.maps:
            hlog.pdebug(space + map.path)
            hlog.pdebug(space + map.maps_type)
            hlog.pdebug(space + map.data_type)

def versioning_parse(file: str, shaders: list[sh.Shader]):
    """Parse maps and store them in VersionShaders.

    Args:
        file (str): File path to a map
        shaders (list[sh.Shader]): List of currently parsed shader

    Returns:
        list[sh.Shader]: Shaders list updated
    """
    
    file_name = os.path.basename(file)
    
    first_key_span = mp.firstKeyWord(file_name)
    if first_key_span is not None:
        shader_name =  file_name[:first_key_span[0]-1]

        found = False
        for shader in shaders:
            if shader.name == shader_name:
                if not isinstance(shader, sh.VersionShader):
                    continue
                shader.parse(file)
                found = True

        if not found:
            newShader = sh.VersionShader(shader_name)
            newShader.parse(file)
            shaders.append(newShader)
            
    return shaders

def general_parse(file: str, shaders: list[sh.Shader]):
    """Parse map and add them to a general Shader.

    Args:
        file (str): File path to a map
        shaders (list[sh.Shader]): List of currently parsed shader

    Returns:
        list[sh.Shader]: Shaders list updated
    """    
    
    file_name = os.path.basename(file)
    
    first_key_span = mp.firstKeyWord(file_name)
    if first_key_span is not None:
        shader_name =  file_name[:first_key_span[0]-1]

        found = False
        for shader in shaders:
            if shader.name == shader_name:
                shader.parse(file)
                found = True

        if not found:
            newShader = sh.Shader(shader_name)
            newShader.parse(file)
            shaders.append(newShader)
            
    return shaders

def get_shaders_from_filepaths(filepaths: list[str]):
    """
    Get each shaders from maps in a directory and his sub directories.

    Format (old): ***_version_name_map-type_signature(_.udim)_(.extension)
    
    Format: mapname_maptype(.udim).extension
    
    Note: The version is expected to be found
    in the base directory of the file.
 
    Args:
    filepaths (str): filepaths list containing maps

    Return:
    list: list of Shader
    """
    ressource.load()

    shaders = []
    for file in filepaths:
        
        # Check if the extension match 
        # with the specified one in the ressource.json
        extension = os.path.splitext(file)[1]
        if (os.path.isdir(file) # Skip if it is a directory
            or extension not in ressource.EXTENSION):
            continue
        
        # Skip thumbnails images
        isThumbnail: bool = False
        for thumbsnails_dir in ressource.THUMBNAILS_DIR:
            if thumbsnails_dir in file:
                isThumbnail = True
                break
        if isThumbnail:
            continue
        
        # Try to get a versions from file path with v#### format
        version_match = re.search(mp.VERSION_PATTERN, file)
        if version_match is None:
            # Parse shader without caring about version
            shaders = general_parse(file, shaders)
        else:
            # Parse shader with versioning (v####)
            shaders = versioning_parse(file, shaders)
        
    return shaders
    

def get_shaders_from_dir(directory_path):
    """
    Get each shaders from maps in a directory and his sub directories.
    
    Args:
    directory_path (str): Path to a directory
    """
    
    directory_path = os.path.abspath(directory_path)
    directory_path = os.path.join(directory_path, "**")
    
    file_list = glob.glob(pathname=directory_path, recursive=True)

    return get_shaders_from_filepaths(file_list)


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

def get_existing_subnet(material_library: hou.Node, shader_name: str):
    """
    Get an existing subnet with the shader's name.

    Args:
    material_library (hou.Node)
    shader_name (str)

    Return:
    hou.Node: Subnet with the shader's name
    """
    
    if not material_library:
        return None
    material_library_subnetworks = material_library.children()
    for subnet in material_library_subnetworks:
        if shader_name in subnet.name():
            return subnet
    return None

def get_shader_from_subnet(subnet: hou.Node):
    """
    Get a sh.Shader from a subnetwork (hou.Node).

    Args:
    subnet (hou.Node)

    Return:
    sh.Shader: Shader object with map parsed from subnetwork.
    """
    
    map_files = []
    for node in subnet.children():
        if node.type().name() == 'mtlximage':
            file_path = node.parm('file').eval()
            file_path = os.path.abspath(file_path)
            map_files.append(file_path)
            
    
    shader = get_shaders_from_filepaths(map_files)
    if len(shader) != 1:
        hlog.pdebug(f"Unexpected number of shaders found.")
        return None
    return shader[0]

def getColor(step, max_step):
    """
    Get a color by getting a the hue at some at over a maximum step.
    In the same way as in #script/kma_mat_from_attr/kma_mat_from_attr.py
    > randomize_base_color(kmb_node, divider).
    """
    
    h = float(step) / float(max_step)
    r, g, b = colorsys.hsv_to_rgb(h, 0.6, 0.9)
    
    return r, g, b

def create_shader_network(
        shader: sh.Shader,
        material_library: hou.Node,
        color: hou.Color=None):
    """
    Create a shader in  material_library.

    Create a subnetwork of material_library, if a subnetwork
    with the shader's name exists, rename the old one as
    "(shader's name)_old". Then bind each maps of the shader to the
    corresponding node.

    Args:
    shader (sh.Shader): Shader to build
    material_library (hou.Node): Material library to store shader.
    color (hou.Color): Color of the subnetwork shader. Default to None.
    """

    # Check existing subnetwork and create a new one if needed
    current_subnet = get_existing_subnet(material_library, shader.name)
    if current_subnet is None and material_library is not None:
        material_library_subnetworks = material_library.children()

        for subnet in material_library_subnetworks:
            if shader.name in subnet.name():
                if not subnet.name().endswith("_old"):
                    subnet.setName(subnet.name() + "_old")

        # Create a new subnetwork for the shader
        mask = voptoolutils.KARMAMTLX_TAB_MASK
        viewer = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        kwargs = {
            "pane":viewer,
            "autoplace":True
        }

        current_subnet:hou.VopNode = voptoolutils.createMaskedMtlXSubnet(
            kwargs,
            shader.name,
            mask,
            "Karma Material Builder",
            "kma")
        if color is not None:
            current_subnet.setColor(color)

    # Create and set each maps
    surface = None
    displacement = None
    for node in current_subnet.children():
        if node.type().name() == 'mtlxstandard_surface':
            surface = node
        if node.type().name() == 'mtlxsurface_unlit':
            surface = node
        if node.type().name() == 'mtlxdisplacement':
            displacement = node


    if not surface:
        hlog.pdebug("Surface not generated.")
        hou.ui.displayMessage("Surface not generated.")
        return

    for map in shader.selected_maps:
        
        already_exist = False
        for image in current_subnet.children():
            map_path = image.parm('file')
            if map_path is None:
                continue
            currentMap = mp.Map(map_path.eval())
            if currentMap is not None and currentMap.parse():
                if currentMap.maps_type == map.maps_type:
                    image.parm('file').set(map.path)
                    already_exist = True
        
        if already_exist:
            continue
        
        node_map = current_subnet.createNode(node_type_name='mtlximage',
                                             node_name=map.name)
        node_map.parm('signature').set(map.signature)
        node_map.parm('file').set(map.path)

        # Plug each map
        out_index = node_map.outputIndex('out')
        in_label = 'in'
        out_label = 'out'

        if map.maps_type == 'normal':
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

def ask_confirmation(shaders: list[sh.Shader]) -> bool:
    if not shaders:
        hlog.pinfo("No shaders selected.")
        hou.ui.displayMessage("No shaders selected.")
        return False
    else:
        hlog.pdebug(str(len(shaders)) + " shaders selected.")

    shaders_infos = ""

    for i, shader in enumerate(shaders):
        shaders_infos += f"Shader {i+1}:\n {shader.name}\n"
        
        shader_maps: list[mp.Map] = shader.selected_maps
        for currentMap in shader_maps:
            if (isinstance(currentMap, mp.VersionMap)):
                shaders_infos += f"--> {currentMap.maps_type} - v{currentMap.version}\n"
            else:
                shaders_infos += f"--> {currentMap.maps_type}\n"
                
        shaders_infos += "="*30+"\n"
        
        if (i != len(shaders)-1):
            shaders_infos += "\n"
    
    confirmation_message = (
        "The following shaders will be created:\n\n" + shaders_infos)
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

    # Start directoy will be current working directory
    start_directory = os.path.join(os.getcwd(), os.sep)

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
    dir_path = hou.ui.selectFile(
        start_directory=start_directory,
        title="Select a directory with textures",
        file_type=hou.fileType.Directory)

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
        create_shader_network(shader, material_library)

    hlog.pinfo("Shaders built.")

    # log_shaders(shaders)
    return
