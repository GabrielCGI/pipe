import os
import maya.cmds as cmds
def setup_autosave():
    autosave_dir = "D:/_save_maya"
    if not os.path.exists(autosave_dir):
        try:
            os.makedirs(autosave_dir)
            destination = 1
        except:
            destination = 0
    if os.path.exists("D:/_save_maya/stop.txt"):
        cmds.autoSave(enable=False)
        print("AUTOSAVE OFF")
        return

    cmds.autoSave(enable=True)
    cmds.autoSave(limitBackups=True)
    cmds.autoSave(maxBackups=5)
    cmds.autoSave(destination=1)  # 1 for local directory
    cmds.autoSave(folder=autosave_dir)
    print("AUTOSAVE ON")
