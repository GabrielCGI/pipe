import maya.cmds as cmds

# ------------------------------MAYA RULES-------------------------------------------

def have_shader_group_well_named(stateManager):
    shading_groups = cmds.ls(type="shadingEngine")
    wrongShaderGroup=[]
    for sg in shading_groups:
        connected_mat = cmds.listConnections(sg + ".surfaceShader", source=True, destination=False)
        if connected_mat:
            mat_name = connected_mat[0]
            expected_sg_name = mat_name + "_mat"
            if sg == expected_sg_name or sg == "initialParticleSE" or sg == "initialShadingGroup" :
                pass
            else:
                wrongShaderGroup.append(sg)
    
    if wrongShaderGroup!=[]:
        return False, f'some shader group have not the good name :{wrongShaderGroup}'
    else:
        return True , f'all shader group are named correctly'

def have_only_geo_at_root(stateManager):
    rootNodesList = cmds.ls(assemblies=True)
    # lets remove all the camera at the root of our maya hierarchy
    cameraList=["persp","top","front","side","geo","left","back","bottom"]
    cameraDetectedList=[]
    for node in rootNodesList:
        if node in cameraList:
            shapes = cmds.listRelatives(node, shapes=True) or []
            shapeTypes = [cmds.nodeType(shape) for shape in shapes]
            if shapeTypes:
                if shapeTypes[0]=="camera":
                    cameraDetectedList.append(node)
    cleanRootNodesList = list(set(rootNodesList)-set(cameraDetectedList))

    if cleanRootNodesList != ['geo']:
        return False , f'there should only have geo at the root of your hierarchy, there is nothing in the root or something else has been detected :{cleanRootNodesList}'
    else:
        return True, 'there is only geo in the root of your hierarchy'