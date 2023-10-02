import os
import shutil
import nuke

def temp_save_before_render(node):
    if node.name() == "Write1":
        global original_file_path  # On stocke le chemin original pour une utilisation ultérieure
        original_file_path = node["file"].getValue()
        node["file"].setValue(os.path.expanduser("~/Desktop/temp_output.jpg"))

def copy_to_final_destination(node):
    if node.name() == "Write1":
        temp_path = os.path.expanduser("~/Desktop/temp_output.jpg")
        
        if os.path.exists(temp_path):
            shutil.copy2(temp_path, original_file_path)
            os.remove(temp_path)
            print "Render completed and copied to %s!" % original_file_path
            node["file"].setValue(original_file_path)  # On restaure le chemin original dans le noeud Write1


nuke.addBeforeRender(temp_save_before_render)
nuke.addAfterRender(copy_to_final_destination)
