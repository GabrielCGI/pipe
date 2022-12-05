import maya.cmds as cmds
def warning(txt):
    cmds.confirmDialog(message= txt)
    cmds.error(txt)

zero_matrix = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]

def match_matrix(source,target):
    m = cmds.xform(source, worldSpace = True, matrix=True, query=True)
    cmds.xform(target,  matrix=m)

def lock_all_transform(obj):
    attr_list = [".tx",".ty",".tz",".rx",".ry",".rz",".sx",".sy",".sz"]
    for attr in attr_list:
        cmds.setAttr(obj+attr,lock =True)
