import hou
import re
import glob

def convert_filename(path):
    pattern = r"(\.(?:jpg|jpeg|tif|tiff|exr|png))$"
    new_path = re.sub(pattern, r"\1.rat", path)
    return new_path

def does_matching_file_exist(new_path):
    search_pattern = new_path.replace('<UDIM>', '????')
    matching_files = glob.glob(search_pattern)
    return len(matching_files) > 0

def is_already_converted(path):
    return path.endswith('.rat')

def convert_to_rat(test_mode=False):
    updated_textures = []
    skipped_textures = []
    already_converted_textures = []

    for node in hou.selectedNodes():
        print(f"Processing Node: {node.path()}")

        for subnode in node.allSubChildren():
            if subnode.type().name() != "mtlximage":
                continue

            filename_parm = subnode.parm('file')
            if not filename_parm:
                continue

            current_path = filename_parm.eval()
            if is_already_converted(current_path):
                already_converted_textures.append((subnode.path(), current_path))
                continue

            new_path = convert_filename(current_path)
            if not does_matching_file_exist(new_path):
                skipped_textures.append((subnode.path(), current_path, new_path))
                continue

            if not test_mode:
                filename_parm.set(new_path)
            updated_textures.append((subnode.path(), current_path, new_path))



    print_summary(updated_textures, skipped_textures, already_converted_textures)

def print_summary(updated_textures, skipped_textures, already_converted_textures):
    print("\nSummary:\n")

    print("Updated Textures:")
    for subnode_path, old_path, new_path in updated_textures:
        print(f"{subnode_path}")
        print(f"{old_path}")
        print(f"{new_path}\n")
    print("-------------------------------")
    print("Skipped Textures:")
    for subnode_path, old_path, new_path in skipped_textures:
        print(f"{subnode_path}")
        print(f"{old_path}")
        print(f"Tried Path: {new_path}\n")
    print("-------------------------------")
    print("Already Converted Textures:")
    for subnode_path, old_path in already_converted_textures:
        print(f"{subnode_path}")
        print(f"{old_path}\n")

# Execute the function with test_mode enabled
convert_to_rat(test_mode=False)
