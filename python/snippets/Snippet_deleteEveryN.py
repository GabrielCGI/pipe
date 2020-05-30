import maya.cmds as cmds
mysel = cmds.ls( selection=True )
inc = 0
for i in mysel:
    if inc <= 2:
        inc = inc+1 
    else:
        print "delete"+i
        inc = 0
    
#cmds.delete( i )
    