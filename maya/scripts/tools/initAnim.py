import os.path
import maya.cmds as cmds

def run():


    # Create the 'assets' group under 'world'
    if not cmds.objExists('assets'):
        assets = cmds.group(em=True, name='assets')
    else:
        assets = 'assets'

    # Create the 'Character' group under 'assets'
    if not cmds.objExists('characters'):
        character = cmds.group(em=True, name='characters', parent=assets)

    # Create the 'Prop' group under 'assets'
    if not cmds.objExists('props'):
        prop = cmds.group(em=True, name='props', parent=assets)

    print("Hierarchy created successfully.")

