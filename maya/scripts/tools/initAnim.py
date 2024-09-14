import os.path
import maya.cmds as cmds

def run():
    # Create the top-level group
    if not cmds.objExists('world'):
        maya_world = cmds.group(em=True, name='world')
    else:
        maya_world = 'world'

    # Create the 'assets' group under 'world'
    if not cmds.objExists('assets'):
        assets = cmds.group(em=True, name='assets', parent=maya_world)
    else:
        assets = 'assets'

    # Create the 'Character' group under 'assets'
    if not cmds.objExists('Characters'):
        character = cmds.group(em=True, name='Characters', parent=assets)

    # Create the 'Prop' group under 'assets'
    if not cmds.objExists('Props'):
        prop = cmds.group(em=True, name='Props', parent=assets)

    print("Hierarchy created successfully.")

