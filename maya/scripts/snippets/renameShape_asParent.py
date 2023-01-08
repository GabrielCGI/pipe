import pymel.core as pm
for i in pm.ls(sl=True):
    child= i.getChildren()
    pm.rename(child,i.name()+"Shape")