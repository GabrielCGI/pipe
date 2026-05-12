import hou
import voptoolutils
import colorsys
import re

print_debug = True
print_info = True


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


def check_selection(selection=None):
    """
    We ask the user to select three nodes: a component geo, a material lib, and a component material.
    It checks that we have what we need to execute the script.

    Return : node componentgeometry, node materiallibrary, node componentmaterial
    """
    if not selection:
        selection = hou.selectedNodes()

    if not len(selection) >= 2:
        hou.ui.displayMessage(
            "Select three nodes : component geometry, material library node and component material."
        )
        return None, None, None

    componentgeometry = []
    materiallibrary = []
    componentmaterial = []

    for node in selection:
        if node.type().name() == "componentgeometry":
            componentgeometry.append(node)
        if node.type().name() == "materiallibrary":
            materiallibrary = node

    # Parse all componentgeometre nodes to find all componentmaterials attached to compententgeometry
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
    # Get node from a specified path
    node = hou.node(node_path)

    if node is None:
        raise ValueError(f"No node found at path: {node_path}")

    # Get node geometry
    geometry = node.geometry()

    # Get list of prim attributes
    primitive_attributes = geometry.primAttribs()

    # Extract the name of these attributes
    attribute_names = [attrib.name() for attrib in primitive_attributes]

    return attribute_names


def clean_str(str):
    clean_str = re.sub(r"[^A-Za-z0-9_-]", "_", str)
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
        # Get node from a given path
        node = hou.node(node_path)

        if node is None:
            raise ValueError(f"No node found at path: {node_path}")

        # list to store material paths
        mtl_list = []

        # Parse node geometry
        geo = node
        if isinstance(geo, hou.SopNode):
            geometry = geo.geometry()
            if geometry:
                # Check if attrib exists
                if geometry.findPrimAttrib(attr):
                    # Get attribute values
                    tmp_mtl_list = []
                    tmp_mtl_list = sorted(
                        list(set(geometry.primStringAttribValues(attr)))
                    )

                    # Format it to be clean :
                    for mtl in tmp_mtl_list:
                        # Take only the last item
                        # Extract the last part of the path
                        last_part = mtl.split(r"/")[-1]

                        # Replace non-alphanumeric characters (except underscore and hyphen) with an underscore, including spaces
                        cleaned_mtl = clean_str(last_part)
                        mtl_list.append(cleaned_mtl)
        mtl_list = list(filter(None, mtl_list))  # Remove empty value
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
        # Get current network view
        network_editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)

        if network_editor is None:
            raise ValueError("No network view found.")

        if node is None:
            raise ValueError(f"Aucun nœud trouvé à l'adresse : {node.path()}")

        # Change current path in network editor
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

    kwargs = {"pane": viewer, "autoplace": True}

    voptoolutils.createMaskedMtlXSubnet(
        kwargs, "karmamaterial", mask, "Karma Material Builder", "kma"
    )
    karma_subnet_node = hou.selectedNodes()[0]
    pdebug("mat nam is: %s" % mtl_name)
    karma_subnet_node.setName(mtl_name, unique_name=True)

    pdebug(karma_subnet_node)
    return karma_subnet_node


def randomize_base_color(kmb_node, step, divider):
    """
    Modify the base color (base_color) of a mtlxstandard_surface node in a Karma Material Builder.
    It will split the Hue into chunk using step/divider, so that we have a nice rainbow of colors! (no unicorn were harmed during the process)
    Args:
        kmb_node (str): The path of the Karma Material Builder node.
    Return:
        r (float), g (float), b (float) : color values
    """

    try:
        # Find the mtlxstandard_surface node
        mtlx_node = None
        for child in kmb_node.children():
            if child.type().name() == "mtlxstandard_surface":
                mtlx_node = child
                break

        if mtlx_node is None:
            raise ValueError(
                "No 'mtlxstandard_surface' node found in the Karma Material Builder."
            )

        # Set the color
        h = float(step) / float(divider)
        r, g, b = colorsys.hsv_to_rgb(h, 0.6, 0.9)

        # Update 'base_color' on the shader
        mtlx_node.parmTuple("base_color").set((r, g, b))

        return r, g, b

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
    component_material_node.parm("nummaterials").set(num_materials)

    # Set path and pattern for mat assignment
    for i, material_name in enumerate(material_names):
        # Set current mat and pattern param
        primpattern_parm = component_material_node.parm(
            f"primpattern{i + 1}"
        )  # primpattern1
        material_path_parm = component_material_node.parm(
            f"matspecpath{i + 1}"
        )  # matspecpath1

        # Mat part
        material_path_parm.set(f"/ASSET/mtl/{material_name}")

        # Use a pattern
        if collectionMode:
            primpattern = f"/ASSET/mtl/collections.collection:mtl_{material_name}"
        else:
            primpattern = f"%type:GeomSubset & *_{material_name}"
        primpattern_parm.set(primpattern)


def create_karma_mat(mtl_list, materiallibrary):
    # Look for the attr on prims and create a list of material names
    
    network_editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    lop_network = network_editor.pwd()
    # check what's inside the material lib node
    children_names = []
    for child in materiallibrary.children():
        children_names.append(child.name())

    # mat are created only if they do not exists
    for i, mtl_name in enumerate(mtl_list):
        if mtl_name not in children_names:
            kma_subnet = create_karma_mat_builder(materiallibrary, mtl_name)

            # set a color for each material, it will split the hue value ladder based on the mat number to create
            rand_color = randomize_base_color(kma_subnet, i, len(mtl_list))

            # Set this color on the mat builder
            node_color = hou.Color(rand_color)
            kma_subnet.setColor(node_color)

        else:
            pinfo(f"Mat name {mtl_name} already exists in {materiallibrary}, skipping")
    network_editor.setPwd(lop_network)
    return mtl_list


def execute(collectionMode=True, sel=None):

    attr = "usdmaterialpath"

    # start to check selection
    componentgeometry, materiallibrary, componentmaterial = check_selection(sel)
    if not componentgeometry and not materiallibrary and not componentmaterial:
        return

    pdebug(componentgeometry)
    pdebug(materiallibrary)
    pdebug(componentmaterial)

    for i in range(len(componentgeometry)):
        ## Search the default node in component geo  :

        default_output_path = f"{componentgeometry[i].path()}/sopnet/geo/default"

        mode = hou.updateModeSetting()
        hou.setUpdateMode(hou.updateMode.Manual)

        mtl_list = get_material_list_from_attr(default_output_path, attr=attr)
        create_karma_mat(mtl_list, materiallibrary)

        how_many_mtl = len(mtl_list)
        pdebug(f"Total mtl: {how_many_mtl}")

        if how_many_mtl > 20:
            cancelUi = hou.ui.displayMessage(
                f"There is {how_many_mtl} materials to create, it will take some time, wanna continue?",
                severity=hou.severityType.ImportantMessage,
                buttons=(
                    "Sure, lets go! (Yes)",
                    "Damn really? I will double check (Cancel)",
                ),
            )
            if cancelUi == 0:
                pass
            else:
                return

        if collectionMode:
            componentgeometry[i].parm("bindmaterials").set("createbind")
            componentgeometry[i].parm("materialbindsubsets").set(0)
        else:
            componentgeometry[i].parm("bindmaterials").set("nobind")
            componentgeometry[i].parm("materialbindsubsets").set(1)
            # componentgeometry.parm("partitionattribs").set("1")
            connect_prim_and_mat(componentmaterial[i], mtl_list, collectionMode=False)

        hou.setUpdateMode(mode)

    print("Set Update Mode back to: %s" % (mode.name()))


if __name__ != "__main__":
    pdebug("\n\n-- New Exec --\n\n")
