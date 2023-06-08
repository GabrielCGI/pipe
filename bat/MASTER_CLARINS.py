import sys
import shutil
import time
import os
if len(sys.argv) > 1:
    print("FOLDER INPUT: " +sys.argv[1])
    print("_______________")
else:
    print("No arguments were provided.")
    raise Exception("This is an error message")

path =sys.argv[1]
render_layer = ["beauty","moustache_mask","contour","mask_moustache"]

for layer in render_layer:
    layer_path = os.path.join(path,layer,"srgb")

    if not os.path.isdir(layer_path):
        print("Not found: "+ layer)
        print("_______________________________")
        continue
    if not "clarins_2301\shots\shot" in layer_path:
        print("abort " + layer_path)
        raise Exception("This is an error message")
    dest_path = layer_path.replace("render_out","render_out_master")
    parts = os.path.normpath(dest_path).split(os.sep)
    parts[0] += "\\"
    parts.pop(-3)
    parts.pop(-1)
    dest_path = os.path.join(*parts)
    print("_______________________________")
    print("Layer: "+ layer)
    print ("DEST PATH: " +dest_path)
    if os.path.isdir(dest_path):
        # Get the current timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        dir_name, file_name = os.path.split(dest_path)
        new_file_name = "zold_"+file_name+"_"+timestamp
        new_dir_path = os.path.join(dir_name, new_file_name)
        # Rename the directory
        print("RENAMING: " +  new_file_name)
        os.rename(dest_path, new_dir_path)
    print("START COPY"")
    shutil.copytree(layer_path, dest_path)
    print("END COPY")
    print("_______________________________")
