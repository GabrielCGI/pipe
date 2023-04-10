import os
import pymel.core as pm

def create_output_paths(texture_path, color_space, render_color_space):
    texture_path = os.path.normpath(texture_path)
    dir_path, file_ext = os.path.splitext(texture_path)
    file_name = os.path.basename(dir_path)

    output_path = os.path.join(
        os.path.dirname(dir_path),
        f"{file_name}_{color_space}_{render_color_space}{file_ext}.tx"
    )
    output_path_legacy = os.path.splitext(texture_path)[0] + ".tx"

    return output_path, output_path_legacy

def replace_to_tx(image_node):
    node_type= image_node.type()
    if node_type == 'file':
        texture_path = image_node.fileTextureName.get()
    elif node_type == 'aiImage':
        texture_path = image_node.filename.get()
    else:
        print(f"Unsupported node type: {node_type}")
        return

    color_space = image_node.colorSpace.get()
    render_color_space = "ACEScg"
    if texture_path.endswith(".tx"):
        print (f"Skipping, already a tx: {texture_path}")
        return

    tx_path, tx_path_legacy = create_output_paths(texture_path, color_space, render_color_space)
    if not os.path.isfile(tx_path) and not os.path.isfile(tx_path_legacy):
        print (f"Skipping, no tx found: {texture_path}")
        return

    image_node.ignoreColorSpaceFileRules.set(1)


    if os.path.isfile(tx_path):
        updated_path = tx_path
    elif os.path.isfile(tx_path_legacy):
        updated_path = tx_path_legacy
    else:
        print(f"No Tx found for {texture_path}")
        return

    if node_type == 'file':
        image_node.fileTextureName.set(updated_path)
    elif node_type == 'aiImage':
        image_node.filename.set(updated_path)

    print(f"Replace {texture_path} -> {updated_path}")

def process_all_tx():
    texture_nodes = pm.ls(type=['file', 'aiImage'])
    for node in texture_nodes:
        replace_to_tx(node)

def find_original_image_file(tx_path):
    possible_extensions = ['.jpg', '.png', '.tiff', '.exr', '.tif']
    base_path = os.path.splitext(tx_path)[0]

    # First, try the new naming convention by removing the "_{color_space}_{render_color_space}.[ORIGINAL_FILE_EXTENTION]" part from the base_path
    base_path_modified = re.sub(r"_[^_]+_[^_]+(\.[^.]+)$", r"\1", base_path)
    if os.path.isfile(base_path_modified):
        return base_path_modified

    # If not found, try the legacy convention by replacing ".tx" with the possible image extensions
    for ext in possible_extensions:
        original_file_path = base_path + ext
        if os.path.isfile(original_file_path):
            return original_file_path

    return None

def replace_by_original(image_node):
    print ('----- %s ------'%(image_node))
    node_type = image_node.type()
    if node_type == 'file':
        texture_path = image_node.fileTextureName.get()
    elif node_type == 'aiImage':
        texture_path = image_node.filename.get()
    else:
        print(f"Unsupported node type: {node_type}")
        return

    if not texture_path.endswith(".tx"):
        print(f"Skipping, not a tx file: {texture_path}")
        return

    original_file_path = find_original_image_file(texture_path)

    if original_file_path is None:
        print(f"No original image file found for {texture_path}")
        return

    if node_type == 'file':
        image_node.fileTextureName.set(original_file_path)
    elif node_type == 'aiImage':
        image_node.filename.set(original_file_path)

    print(f"Replace {texture_path} -> {original_file_path}")

# To test the function
def process_all_original():
    texture_nodes = pm.ls(type=['file', 'aiImage'])
    for node in texture_nodes:
        replace_by_original(node)
