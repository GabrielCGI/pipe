import maya.cmds as cmds

number = 1

def multi_import_ref(path, number):
    for i in range(number):
        cmds.file(path, r=True)


def multiImport():
    basicFilter = "*.ma *.mb *.obj *.fbx *.abc *.ass"
    listRef = cmds.fileDialog2(fileFilter=basicFilter, dialogStyle=2, fileMode=4)


    result = cmds.promptDialog(
                    title='X Refs',
                    message='Import references multiple time. \n How many?:',
                    button=['Import', 'Cancel'],
                    defaultButton='OK',
                    cancelButton='Cancel',
                    dismissString='Cancel')
    if result == 'Import':
        number = int(cmds.promptDialog(query=True, text=True))
        try:
            for ref in listRef:
                print ref
                multi_import_ref(ref, number)
        except:
            cmds.warning( "%s: Reference failed"%ref )

def replaceByReferences():
        sel = cmds.ls(selection=True)
        basicFilter = "*.ma *.mb *.obj *.fbx *.abc *.ass"
        ref = cmds.fileDialog2(fileFilter=basicFilter, dialogStyle=2, fileMode=1)
        for s in sel:
            a = cmds.file(ref[0], r=True)
            cmds.file( a, sa=True)
            objects = cmds.ls(selection=True)

            for obj in objects:
                if cmds.nodeType(obj) == "transform":
                    cmds.matchTransform(obj,s)
        cmds.select(sel)
