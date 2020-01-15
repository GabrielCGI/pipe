import maya.cmds as mc

def hierarchyTree(mparent, tree):
    children = mc.listRelatives(mparent, c=True, type='joint')

    if children:
        tree[mparent] = (children, {})
        for child in children:
            hierarchyTree(child, tree[mparent][1])
            
            

top_node =  mc.ls(sl=True)[0]  # could also use mc.ls(sl=True)[0] if you want...
hierarchy_tree = {}
my = hierarchyTree(top_node, hierarchy_tree)
print hierarchy_tree
