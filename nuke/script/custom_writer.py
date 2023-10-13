import os
import shutil
import nuke

def run_before():
    global currentNode
    global original_file_path
    global temp_path

    currentNode = nuke.thisNode()
    original_file_path = nuke.filename(currentNode)

    base_filename = os.path.basename(original_file_path)
    sanitized_base_filename = base_filename.replace("#", "")

    temp_dir = os.path.join(os.environ["TEMP"], "local_writes_temp_" + sanitized_base_filename)
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    temp_path = os.path.join(temp_dir, base_filename)
    temp_path = temp_path.replace('\\', '/')

def run_before_each_frame():
    if nuke.filename(currentNode) != temp_path:
        currentNode["file"].setValue(temp_path)

def run_after_each_frame():
    global temp_dir

    sanitized_base_filename = os.path.basename(original_file_path).replace("#", "")
    temp_dir = os.path.join(os.environ["TEMP"], "local_writes_temp_" + sanitized_base_filename)

    for filename in os.listdir(temp_dir):
        temp_file_path = os.path.join(temp_dir, filename)
        destination_path = os.path.join(os.path.dirname(original_file_path), filename)
        
        shutil.copy2(temp_file_path, destination_path)

        os.remove(temp_file_path)


    if nuke.filename(currentNode) != original_file_path:
        currentNode["file"].setValue(original_file_path.replace('\\', '/'))

def run_after():
    shutil.rmtree(temp_dir)

