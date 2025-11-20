# Copyright © 2024 Valentin Dornel

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Script created by Valentin "ValDo" Dornel, at Illogic Studios
v1.0 (tested on H20.0.688): 2024-07-10

Description :
By selecting the nodes of the component builder, the script will fetch values
of a prim attribute (such as shop_materialpath) on the default output node of the component geometry (ie : /stage/componentgeometry/sopnet/geo/default)
It will create a named karma material builder for each attr with a random color
then create a shader assignment preset on the component material.

I'm not a programmer, at least half of the code is done by ChatGPT and parts could be improved for sure!

We can put this script in a shelf button like this:
import sys
sys.path.append(r"R:\pipeline\pipe\houdini\scripts\kma_mat_from_attr")
import kma_mat_from_attr
kma_mat_from_attr.execute()

"""

__author__ = "Valentin ValDo Dornel"
__credits__ = ["Gabriel Grapperon"]
__license__ = "MIT License 2024"
__version__ = "1.1"
__status__ = "Production"

# editer par frédéric dewit  pourquoi ?: pouvoir l'executer plusieur avec une selection multiple 

import hou
import voptoolutils
import colorsys
import re

print_debug=True
print_info=True

def pinfo(toPrint):
    if print_info is True:
        print("info - " + str(toPrint))
    else:
        pass

def pdebug(toPrint):
    if print_debug is True:
        print("debug - " + str(toPrint))
    else:
        pass

def check_selection():
    """
    We ask the user to select three nodes: a component geo, a material lib, and a component material.
    It checks that we have what we need to execute the script.

    Return : node componentgeometry, node materiallibrary, node componentmaterial
    """

    selection= hou.selectedNodes()
    if not len(selection)>=2:
        hou.ui.displayMessage("Select three nodes : component geometry, material library node and component material.")
        return None, None, None
    
    componentgeometry = []
    materiallibrary   = []
    componentmaterial = []

    for node in selection:
        if node.type().name()=="componentgeometry":
            componentgeometry.append(node)
        if node.type().name()=="materiallibrary":
            materiallibrary = node


    # parser tout les node componentgeometry pour trouver les componentmaterial qui sont ratacher aux componentgeometry
    for node in componentgeometry:
        Dref = node
        for _ in range(5):
            Dref = Dref.outputs()[0]
            if Dref.type().name() == "componentmaterial":
                componentmaterial.append(Dref)
                break

    
    if not componentgeometry and not materiallibrary:
        hou.ui.displayMessage("Error while finding nodes, check your selection")
        return None, None, None
    if len(componentgeometry) != len(componentmaterial):
        hou.ui.displayMessage("Error while finding nodes, check your selection")
        return None, None, None
        
    return componentgeometry, materiallibrary, componentmaterial

def list_primitive_attributes(node_path):
    # Obtenir le nœud à partir du chemin spécifié
    node = hou.node(node_path)

    if node is None:
        raise ValueError(f"No node found at path: {node_path}")

    # Obtenir la géométrie du nœud
    geometry = node.geometry()

    # Obtenir la liste des attributs primitifs
    primitive_attributes = geometry.primAttribs()

    # Extraire les noms des attributs
    attribute_names = [attrib.name() for attrib in primitive_attributes]

    return attribute_names

def build_collection(node_path, attr, componentgeometry, componentmaterial):
    """
    Builds a sequence of collection nodes based on geometry attributes
    Each collection node corresponds to a unique material and includes paths of primitives that use this material.

    Parameters:
    node_path (str): The path to the Houdini node where geometry is fetched.
    attr (str): The attribute name used to fetch material paths from geometry primitives.
    componentgeometry (hou.Node): The Houdini node that serves as the starting point of the collection nodes.
    componentmaterial (hou.Node): The Houdini node where the final collection node connects to continue the network flow.

    """
    pdebug("Node path: %s"%(node_path))
    node = hou.node(node_path)
    pdebug(node)

    stage_context = hou.node("/stage")


    geo = node.geometry()
    pdebug(geo)
    names = None
    # Get names and material paths from geometry primitive attributes
    try:
        names = geo.primStringAttribValues("path")
    except: 
        pdebug("Fail to get geo.primStringAttribValues('path') ")

    if names == None:

        try:   
            names = geo.primStringAttribValues("name")
        except: 
            pdebug("Fail to get geo.primStringAttribValues('name') ")
    if names == None:

        try:   
            names = geo.primStringAttribValues("usdprimpath")
            pdebug("USD PRIM PATH FOUND ")
        except: 
            pdebug("Fail to get geo.primStringAttribValues('usdprimpath') ")
            pdebug("FAIL ! IT's MISSING PRIM ATTRIBUT ON THE OBJECT: PATH, NAME, OR USDPIMPATH")

            return 

    materials = geo.primStringAttribValues(attr)
    # Dictionary to hold material keys and sets of names as values
    material_name_dict = {}

    # Iterate over names and materials and populate the dictionary
    for material, name in zip(materials, names):
        if material not in material_name_dict:
            material_name_dict[material] = set()
        material_name_dict[material].add(name)

    # Get the parent node where to create collection nodes
    parent_node = node.parent()

    # Variable to keep track of the last created collection node
    previous_node = None
    first_node = None

    # Creating a collection node for each material
    for material, paths in material_name_dict.items():
        # Generate a legal node name by replacing non-alphanumeric characters
        last_part = material.split(r"/")[-1]
        node_name = "mtl_" + clean_str(last_part)

        # Create the collection node
        pdebug(f"Trying to create collection node {node_name } ")
        set_network_view_path(stage_context)
        collection_node = stage_context.createNode("collection", node_name=node_name)

        pinfo(f"Collection node {collection_node } created !")

        sort_paths = sorted(paths)
        # Set the include pattern to the list of paths for this material
        include_pattern = "*"+" \n*".join(sort_paths)
        collection_node.parm('includepattern1').set(include_pattern)
        collection_node.parm('collectionname1').set(node_name)
        collection_node.parm("defaultprimpath").set("/ASSET/mtl/collections")

        # Connect the previous node's output to the current node's input if previous node exists
        if previous_node:
            collection_node.setInput(0, previous_node)
        if not first_node:
            first_node = collection_node

        # Update previous_node to the current node
        previous_node = collection_node
    #Connect nodes
    first_node.setInput(0,componentgeometry)
    componentmaterial.setInput(0,collection_node)
    first_node.parent().layoutChildren()

def clean_str(str):
    clean_str = re.sub(r'[^A-Za-z0-9_-]', '_', str)
    return clean_str

def get_material_list_from_attr(node_path, attr="usdmaterialpath"):
    """
    Retrieve the values of an attribute (ie: shop_materialpath) from a given node.

    Args:
    node_path (str): path of the Houdini node.

    Returns:
    list: A list of unique values of the attribute, without any weird characters, sorted
    """
    try:
        # Récupérer le nœud à partir du chemin fourni
        node = hou.node(node_path)

        if node is None:
            raise ValueError(f"No node found at path: {node_path}")

        # Initialiser une liste pour stocker les chemins des matériaux
        mtl_list = []

        # Parcourir les géométries contenues dans le nœud
        geo = node
        if isinstance(geo, hou.SopNode):
            geometry = geo.geometry()
            if geometry:
                # Vérifier si l'attribut shop_materialpath existe
                if geometry.findPrimAttrib(attr):
                    # Récupérer les valeurs de l'attribut shop_materialpath
                    tmp_mtl_list = []
                    tmp_mtl_list = sorted(list(set(geometry.primStringAttribValues(attr))))

                    #format it to be clean :
                    for mtl in tmp_mtl_list:
                        # take only the last item
                        # Extract the last part of the path
                        last_part = mtl.split(r"/")[-1]

                        # Replace non-alphanumeric characters (except underscore and hyphen) with an underscore, including spaces
                        cleaned_mtl = clean_str(last_part)
                        mtl_list.append(cleaned_mtl)
        mtl_list = list(filter(None, mtl_list)) # Remove empty value
        return mtl_list

    except Exception as e:
        print(f"Error: {e}")
        return []

def set_network_view_path(node):
    """
    Change the current path of the Network View in Houdini.

    Args:
    new_path (str): The new path to set in the Network View.
    """

    try:
        # Récupérer le network view en cours
        network_editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)

        if network_editor is None:
            raise ValueError("No network view found.")

        # Récupérer le nœud à partir du nouveau chemin fourni
        new_node = node

        if node is None:
            raise ValueError(f"Aucun nœud trouvé à l'adresse : {node.path()}")

        # Changer le chemin courant de l'éditeur de réseau
        network_editor.setPwd(node)

    except Exception as e:
        print(f"Error : {e}")

def create_karma_mat_builder(material_library_node, mtl_name):
    """
    This function is somehow a hack that only works using the viewport interaction,
    so we force the network view to be teleported inside a LOP Material context where we want to create the karma mat builder
    most of the time it should be inside a material library
    """
    pdebug("Start work on karma mat builder")
    set_network_view_path(material_library_node)

    mask = voptoolutils.KARMAMTLX_TAB_MASK

    viewer = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)

    kwargs = {
        "pane":viewer,
        "autoplace":True
    }

    voptoolutils.createMaskedMtlXSubnet(kwargs,"karmamaterial",mask,"Karma Material Builder", "kma")
    karma_subnet_node = hou.selectedNodes()[0]
    pdebug("mat nam is: %s"%mtl_name)
    karma_subnet_node.setName(mtl_name, unique_name=True)

    pdebug(karma_subnet_node)
    return karma_subnet_node

def randomize_base_color(kmb_node, step, divider):
    """
    Modify the base color (base_color) of a mtlxstandard_surface node in a Karma Material Builder.
    It will split the Hue into chunk using step/divider, so that we have a nice rainbow of colors! (no unicorn were harmed during the process)
    Args:
    kmb_node (str): The path of the Karma Material Builder node.
    Return the color
    """

    try:
        # find the mtlxstandard_surface node
        mtlx_node = None
        for child in kmb_node.children():
            if child.type().name() == "mtlxstandard_surface":
                mtlx_node = child
                break

        if mtlx_node is None:
            raise ValueError("No 'mtlxstandard_surface' node found in the Karma Material Builder.")

        # Set the color
        h = float(step)/float(divider)
        r, g, b = colorsys.hsv_to_rgb(h,0.6,0.9)

        # Update 'base_color' on the shader
        mtlx_node.parmTuple('base_color').set((r,g,b))

        return r,g,b

    except Exception as e:
        print(f"Error : {e}")

def connect_prim_and_mat(component_material_node, material_names, collectionMode=True):
    """
    Update material assignments for a component material node in Houdini.

    Args:
    component_material_node_path (str): The path of the component material node.
    material_names (list): A list of material names.
    """

    # Creates one entry for each material list on the component material

    # Init number of material assignments :
    num_materials = len(material_names)

    # Update param 'num_materials'
    component_material_node.parm('nummaterials').set(num_materials)

    # Set path and pattern for mat assignment
    for i, material_name in enumerate(material_names):
        # Set current mat and pattern param
        primpattern_parm = component_material_node.parm(f'primpattern{i+1}') #primpattern1
        material_path_parm = component_material_node.parm(f'matspecpath{i+1}') #matspecpath1

        # Mat part
        material_path_parm.set(f'/ASSET/mtl/{material_name}')

        # Use a pattern
        if (collectionMode==True):
            primpattern = f'/ASSET/mtl/collections.collection:mtl_{material_name}'
        else:
            primpattern = f'%type:GeomSubset & *_{material_name}'
        primpattern_parm.set(primpattern)

def create_karma_mat(default_output_path, attr, materiallibrary):
    # Look for the attr on prims and create a list of material names
    mtl_list = get_material_list_from_attr(default_output_path, attr=attr)
    network_editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    lop_network = network_editor.pwd()
    # check what's inside the material lib node
    children_names = []
    for child in materiallibrary.children():
        children_names.append(child.name())

    # mat are created only if they do not exists
    for i,mtl_name in enumerate(mtl_list):
        if mtl_name not in children_names:
            #pdebug(f"creating mtl_name: {mtl_name}")
            kma_subnet = create_karma_mat_builder(materiallibrary, mtl_name)

            # set a color for each material, it will split the hue value ladder based on the mat number to create
            rand_color = randomize_base_color(kma_subnet, i, len(mtl_list))

            # Set this color on the mat builder
            node_color = hou.Color(rand_color)
            kma_subnet.setColor(node_color)


        else :
            pinfo(f"Mat name {mtl_name} already exists in {materiallibrary}, skipping")
    network_editor.setPwd(lop_network)
    return mtl_list

def execute(collectionMode=True):
    """
    Main execution function
    """
    attr = "usdmaterialpath"
    

    # start to check selection
    componentgeometry, materiallibrary, componentmaterial=check_selection()
    if not componentgeometry and not materiallibrary and not componentmaterial:
        return

    pdebug(componentgeometry)
    pdebug(materiallibrary)
    pdebug(componentmaterial)

    for i in range(len(componentgeometry)):
        ## Search the default node in component geo  :
        
        default_output_path = f"{componentgeometry[i].path()}/sopnet/geo/default"


        ### Create a window to ask to the attr to create mat from
        # Define the dropdown menu options
        # attrs = list_primitive_attributes(default_output_path)
        # Show the dropdown dialog
        # choice = hou.ui.selectFromList(attrs, exclusive=True, title="Choose an Option", message="Choose an attribute to create material from. One mat will be created per attribute")

        # Check if the user made a choice
        # if choice:
        #     attr = attrs[choice[0]]
        # else:
        #     return
        
        mode = hou.updateModeSetting()
        hou.setUpdateMode(hou.updateMode.Manual) 
        mtl_list=create_karma_mat(default_output_path, attr, materiallibrary)
        how_many_mtl = len(mtl_list)
        pdebug(f"Total mtl: {how_many_mtl}")
        if how_many_mtl>20:
            cancelUi = hou.ui.displayMessage(f"There is {how_many_mtl} materials to create, it will take some time, wanna continue?", severity = hou.severityType.ImportantMessage, buttons=('Sure, lets go! (Yes)','Damn really? I will double check (Cancel)'))
            if cancelUi==0:
                pass
            else:
                return
            
        if (collectionMode==True):
            componentgeometry[i].parm('bindmaterials').set("createbind")
        else:
            componentgeometry[i].parm('bindmaterials').set("nobind")
            componentgeometry[i].parm('materialbindsubsets').set(1)
            #componentgeometry.parm("partitionattribs").set("1")
            connect_prim_and_mat(componentmaterial[i], mtl_list, collectionMode=False)
        
        hou.setUpdateMode(mode)
    
    print("Set Update Mode back to: %s"%(mode.name()))

if __name__ != "__main__":
    pdebug("\n\n-- New Exec --\n\n")
