import pymel.core as pm


#MAYA FIRST
#ZBRUSH SECONDE

# Get selected objects
sel = pm.ls(selection=True)

# Check that exactly two objects are selected
if len(sel) != 2:
    pm.warning('Please select exactly two objects.')
else:
    # Get the first and second selected objects
    obj1 = sel[0]
    obj2 = sel[1]
    
    # Copy UVs from obj1 to obj2

    pm.transferAttributes(obj1, obj2, transferUVs=1,sampleSpace=5,searchMethod=3 )
    pm.delete(sel, constructionHistory = True)
    
    # Create blendshape from obj2 to obj1
    blendshape = pm.blendShape(obj2, obj1)[0]
    
    # Set blendshape weight to 1
    pm.setAttr(blendshape + '.' + obj2.name().split(":")[-1], 1)
    pm.delete(sel, constructionHistory = True)