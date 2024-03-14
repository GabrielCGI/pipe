import maya.cmds as cmds
import json
import os

# Data structure to hold all shader information
all_shaders_data = {}

# Get all shaders in the scene
shaders = cmds.ls(materials=True)

for shader in shaders:
    # Check if the shader is an aiStandardSurface shader
    if cmds.nodeType(shader) == 'aiStandardSurface':
        # Get Transmission Weight and Transmission Color
        transmission_weight = cmds.getAttr(shader + '.transmission')
        transmission_color = cmds.getAttr(shader + '.transmissionColor')[0]  # Returns a tuple
        baseColor = cmds.getAttr(shader + '.baseColor')[0]
        specularIOR = cmds.getAttr(shader + '.specularIOR')
        specularRoughness = cmds.getAttr(shader + '.specularRoughness')
        metalness = cmds.getAttr(shader + '.metalness')

        # Add shader data to the dictionary
        all_shaders_data[shader] = {
            'transmission_weight': transmission_weight,
            'transmission_color': transmission_color,
            'base_color': transmission_color,
            'specularIOR': specularIOR,
            'specularRoughness': specularRoughness,
            'metalness' : metalness


        }

# Define the JSON file path
json_file_path = 'D:/aiStandardSurface_shaders.json'  # Update this path

# Write all shader data to a single JSON file
with open(json_file_path, 'w') as json_file:
    json.dump(all_shaders_data, json_file, indent=4)

print(f'All shader data written to {json_file_path}')
