# This script will be executed after the execution of an render state in the Prism State Manager.
# You can use this file to define project specific actions, like modifying the created images.

# Example:
# print "Prism has rendered images."

# If the main function exists in this script, it will be called.
# The "kwargs" argument is a dictionary with usefull information about Prism and the current export.

def main(*args, **kwargs):
    
    core = kwargs["core"]
    
    if core.appPlugin.pluginName == "Houdini":
        import hou
        
        # Only proceed if GUI is available
        if not hou.isUIAvailable():
            print("Houdini is not in GUI mode. Skipping ranchExporter in postRender.")
            return
        else: 
            print("Houdini is  in GUI mode. Starting ranchExporter in post Render.")

            import threading
            import ranchExporter

            thread = threading.Thread(target=ranchExporter.parseAndCopyToRanch, args=(kwargs,))
            thread.start()