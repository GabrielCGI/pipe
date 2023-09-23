import os
import pymel.core as pm

input_path = r"R:\megascan\Downloaded\3d\wood_tool_udrqbbyqx"

def assign_shader(obj, obj_path):

	#Dict for hypdershade nodes
    nodes_dict = {
        'place2dTexture': 'place2dTexture',
        obj + '_shader': 				'aiStandardSurface',
        obj + '_shader_Color': 			'file',
        obj + '_shader_Metalness': 		'file',
        obj + '_shader_SpecRoughness': 	'file',
        obj + '_shader_Normal': 		'file',
        obj + '_shader_Diplace': 		'file',

        obj + '_aiColorCorrect': 		'aiColorCorrect',
        obj + '_remapValue': 			'remapValue',
        obj + '_aiNormalMap': 			'aiNormalMap',
        obj + '_displacementShader': 	'displacementShader'
    }

    # Dict for file nodes
    texture_mapping = {
        "Color": 			"_4K_Albedo",
        "SpecRoughness": 	"_4K_Roughness",
        "Metalness": 		"_4K_Metalness",
        "Normal": 			"_4K_Normal_LOD0",
        "Diplace": 			"_4K_Displacement"
    }

    # Nodes creations as shader nodes or as utility nodes
    created_nodes = {}
    for name, node_type in nodes_dict.items():
        if "Shader" in node_type or "Surface" in node_type:
            created_nodes[name] = pm.shadingNode(node_type, asShader=True, name=name)
        else:
            created_nodes[name] = pm.shadingNode(node_type, asUtility=True, name=name)

    # Shading group creation
    shading_group = pm.sets(renderable=True, noSurfaceShader=True, empty=True, name=created_nodes[obj +'_shader'] + "SG")

    # Connect and edit "file" nodes
    for name, node in created_nodes.items():
        if pm.objectType(node) == 'file':

            pm.connectAttr(created_nodes['place2dTexture'].outUV, node.uvCoord)
            pm.setAttr(node.uvTilingMode, 3)

            # Connect to existing texture maps
            texture_map = name.rsplit("_", 1)[-1]
            texture_name = texture_mapping.get(texture_map)
            if texture_name:

                # Check if .exr version exists. Else, assign .jpg version
                if os.path.exists(obj_path + texture_name + ".exr"):
                    pm.setAttr(node.fileTextureName, obj_path + texture_name + ".exr")
                    print("connected : " + obj_path + texture_name + ".exr")

                else:
                    if os.path.exists(obj_path + texture_name + ".jpg"):
                        pm.setAttr(node.fileTextureName, obj_path + texture_name + ".jpg")
                        print("connected : " + obj_path + texture_name + ".jpg")


    # Connect nodes based on functionality
    pm.connectAttr(created_nodes[obj + '_shader_Color'].outColor, created_nodes[obj +'_aiColorCorrect'].input)
    pm.connectAttr(created_nodes[obj + '_shader_SpecRoughness'].outColorR, created_nodes[obj +'_remapValue'].inputValue)
    pm.connectAttr(created_nodes[obj + '_shader_Normal'].outColor, created_nodes[obj +'_aiNormalMap'].input)
    pm.connectAttr(created_nodes[obj + '_shader_Diplace'].outColorR, created_nodes[obj +'_displacementShader'].displacement)
    pm.connectAttr(created_nodes[obj + '_aiColorCorrect'].outColor, created_nodes[obj +'_shader'].baseColor)
    pm.connectAttr(created_nodes[obj + '_shader_Metalness'].outColorR, created_nodes[obj +'_shader'].metalness)
    pm.connectAttr(created_nodes[obj + '_remapValue'].outValue, created_nodes[obj +'_shader'].specularRoughness)
    pm.connectAttr(created_nodes[obj + '_aiNormalMap'].outValue, created_nodes[obj +'_shader'].normalCamera)

    # Connect nodes to Shading group
    pm.connectAttr(created_nodes[obj +'_shader'].outColor, shading_group.surfaceShader, force=True)
    pm.connectAttr(created_nodes[obj +'_displacementShader'].displacement, shading_group.displacementShader, force=True)

    # Assign shader
    pm.select(obj)
    pm.hyperShade(assign=shading_group)

# For 3d objects
def load_object(path):
    object_name = path.rsplit("_", 1)[-1]

    #get objs in scene before import
    objs_before = set(pm.ls(dag=True, long=True))

    # .fbx files listing
    fbx_files = [f for f in os.listdir(path) if f.startswith(object_name) and f.endswith('.fbx')]
    if fbx_files:

    	# Import first matching file
        pm.importFile(os.path.join(path, fbx_files[0]))
        # Get imported objs
        new_objs = set(pm.ls(dag=True, long=True)) - objs_before

        # Rename and assign shader
        for obj in new_objs:
            if pm.objectType(obj) == "transform":
                pm.rename(obj, object_name)
                assign_shader(obj, os.path.join(path, object_name))


def identify(path):
    if "3dplant" in path:
        print('3dplant')
    elif "3d" in path:
        load_object(path)
    else:
        print("surface")


identify(input_path)