import pymel.core as pm

# Get a list of all selected objects


# Iterate over each selected object
def merge_uv(obj):
    default_uv = pm.getAttr(obj.name()+".uvSet[0].uvSetName")
    try:
        pm.polyUVSet(obj, rename=True, newUVSet='map1', uvSet=default_uv)
    except:
        pass
    try:
        default_uv = pm.getAttr(obj.name()+".uvSet[0].uvSetName")
        # Get the current UV set
        current_uv_set = pm.polyUVSet(query=True, currentUVSet=True)[0]

        uvs = pm.polyListComponentConversion(obj, toUV=True)
        # Copy the current UV set to the default UV set
        pm.polyCopyUV( uvs, uvi= current_uv_set, uvs=default_uv )


        # Rename the default UV set to "map1"


        # Delete all UV sets except the default
        for uv_set in pm.polyUVSet(obj, q=1, allUVSets=1):
            if uv_set != "map1":
                pm.polyUVSet( delete=True, uvSet=uv_set)
    except:
        print ("fail on %s"%obj.name())
selected_object = pm.ls(selection=True)[0]
mshs = pm.listRelatives(selected_object, allDescendents=True,shapes=True)

for obj in mshs:
    merge_uv(obj)
