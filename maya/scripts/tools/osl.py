import pymel.core as pm

# Create a camera in spherical mode named "HDRI_CAM"
camera_hdri = pm.camera(name="HDRI_CAM")[0]
camera_hdri.aiTranslator.set("spherical")

# Set image size to 2000 width and height 1000


# Create a cube named "PROJECT_CUBE"
project_cube = pm.polyCube(name="PROJECT_CUBE")

# Create a aiOsl shader and load the osl shader
aiOslShader = pm.shadingNode('aiOslShader', asShader=True)
aiOslShader.code_cache.set("shader emit(\n    color EmitColor = color(1, 1, 1),\n    float Intensity = 1,\n    output closure color CL=emission(\"label\",\"mytag\")\n)\n{\n    CL = emission(\"label\",\"customEmit\") * EmitColor * Intensity;\n}")
# Create a file node
file_node = pm.shadingNode('file', asTexture=True)

# Create a aiUvProjection and set projection type to spherical
aiUvProjection = pm.shadingNode('aiUvProjection', asTexture=True)
pm.setAttr(aiUvProjection.projectionType, 1)

# Connect the out color of the file node to the aiProject node .projectionColor attribute
pm.connectAttr(file_node + '.outColor', aiUvProjection + '.projectionColor')

# Connect the out color of the projection node to the .EmitColor attribute of the osl shader
#pm.connectAttr(aiUvProjection + '.outColor', aiOslShader + '.EmitColor')

# Connect the inverse world matrix of the "HDRI_CAM" to the placement matrix of the aiUvProjection (.placementMatrix)
pm.connectAttr(camera_shape + '.worldInverseMatrix', aiUvProjection + '.placementMatrix')
