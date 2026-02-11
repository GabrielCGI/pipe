import maya.cmds as cmds
from functools import partial

#--------------------------------------------------------------------
def getTextField(textField, *args):

    textField = cmds.textField(textField, q=True, text=True)
    return textField

def getCheckBox(checkBox, *args):

    checkBox = cmds.checkBox(checkBox, q=True, v=True)
    return checkBox

def getDropdownMenu(menu, *args):

    menuSelection = cmds.optionMenu(menu, q=True, select=True)
    return menuSelection

#--------------------------------------------------------------------
def matchCameras(*args):

    # Get TextField Input
    nameSpace = getTextField('namespace_textField', *args)

    # Get CheckBox
    checkBox = getCheckBox('focal_checkBox', *args)

    # Get falloff menu 
    menuSelection = getDropdownMenu('controller_menu', *args)

    # Debug Log
    print('\nDEBUG LOG:\n')
    print(f'Text Field: {nameSpace} \nCheck Box: {checkBox} \nController: {menuSelection}')

    # Select Controller
    if menuSelection == 2:
        controller = 'ctrl_root'
    else:
        controller = 'ctrl_general'

    # Match Camera Transforms
    cmds.matchTransform(f'{nameSpace}:{controller}', 'persp')

    # Match Focal
    if checkBox == True:
        focal = cmds.getAttr('persp.focalLength')
        cmds.setAttr(f'{nameSpace}:ctrl_options.focal', focal)

#--------------------------------------------------------------------
def main():
    matchCamerasWindow = cmds.window(title='Match Cameras', widthHeight=(220, 150), s=False, mnb=False, mxb=False)

    runLayout = cmds.columnLayout(adj=True)
    optionLayout = cmds.columnLayout(adj=False)
    textLayout = cmds.columnLayout(adj=False)

    #------------------------------------------
    cmds.setParent(textLayout)

    cmds.separator(style='none', h=10)
    cmds.rowColumnLayout(numberOfColumns=2)
    cmds.text(label='Namespace: ')
    cmds.textField('namespace_textField', text='camRig_Rigging', width=140)
    cmds.separator(style='none', h=10)
    cmds.text(label=' ') # UI Layout spaceholder for 2 column layout
    cmds.text(label='Match Focal: ')
    cmds.checkBox('focal_checkBox', label=' ', value=True)

    #------------------------------------------
    cmds.setParent(optionLayout)

    cmds.separator(style='none', h=10)
    cmds.optionMenu('controller_menu', label='Controller: ')
    cmds.menuItem(label='General')
    cmds.menuItem(label='Root')

    #------------------------------------------
    cmds.setParent(runLayout)

    cmds.separator(style='in', h=20)
    cmds.button(l='Match Cameras', c=partial(matchCameras))

    #------------------------------------------

    cmds.showWindow(matchCamerasWindow)