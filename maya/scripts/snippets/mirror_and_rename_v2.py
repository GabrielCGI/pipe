import pymel.core as pm

# Get the current selection
selection = pm.ls(selection=True)[0]

# Duplicate the selection
duplicateGrp = pm.duplicate(selection)[0]

for obj in duplicateGrp:
    for a in pm.listAttr(obj):
        obj.attr(a).unlock()
# Scale the duplicates by -1 on the X axis
pm.scale(1, -1, 1 )

# Freeze the transformations on the duplicates
pm.makeIdentity(duplicateGrp, apply=True, t=1, r=1, s=1, n=0, pn=1)

name = duplicateGrp.name()

name =name.split("_R_")
name = "_L_".join(name)
duplicateGrp.rename(name)
# Rename the duplicates by appending "R" to the last character of the name
