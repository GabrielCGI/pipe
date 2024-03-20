import maya.cmds as cmds
import json
import os
import pymel.core as pm
import random
import string


def renameNamespacesToRandom():
    # Function to generate a unique 5-character string
    def generateUniqueName(existingNames):
        while True:
            newName = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
            if newName not in existingNames:
                return newName

    # Get all namespaces except for the root and UI namespaces, which cannot be renamed
    allNamespaces = [ns for ns in pm.namespaceInfo(listOnlyNamespaces=True, recurse=True) if ns not in ['UI', 'shared']]

    # Sort namespaces by depth, so we rename children before parents to avoid conflicts
    allNamespaces.sort(key=lambda x: x.count(':'), reverse=True)

    renamedNamespaces = set()

    for ns in allNamespaces:
        # Generate a unique new namespace name
        newNs = generateUniqueName(renamedNamespaces)

        # Rename the namespace
        pm.namespace(rename=[ns, newNs])
        print(f"Renamed namespace from {ns} to {newNs}")

        # Keep track of the new namespace names to ensure uniqueness
        renamedNamespaces.add(newNs)

# Execute the function to start the renaming process

def importAllReferences():
    # Initially, check for the presence of references
    refs = pm.listReferences()
    # While there are references in the scene
    while refs:
        # Import each reference found
        for ref in refs:
            # This command removes the encapsulation of the reference,
            # making its contents part of the current scene.
            ref.importContents()
        # Recheck for references after imports, to catch new ones if any were added
        refs = pm.listReferences()

# Call the function to start the import process

def redirectAiSurfaceShaderToSurfaceShader():
    # Get all shading groups in the scene
    shadingGroups = pm.ls(type='shadingEngine')

    for sg in shadingGroups:
        # Check if there's a connection to the aiSurfaceShader attribute
        aiSurfaceShaderConnections = sg.aiSurfaceShader.listConnections(p=True)

        if aiSurfaceShaderConnections:
            # There's at least one input connection to aiSurfaceShader
            for connection in aiSurfaceShaderConnections:
                # Disconnect the current connection


                # Connect the input to the surfaceShader attribute instead
                pm.connectAttr(connection, sg.surfaceShader, force=True)

                print(f"Redirected connection from {connection} to surfaceShader of {sg.name()}")

# Execute the function

def exportJson():
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
            transmissionDispersion = cmds.getAttr(shader + '.transmissionDispersion')
            # Add shader data to the dictionary
            all_shaders_data[shader] = {
                'transmission_weight': transmission_weight,
                'transmission_color': transmission_color,
                'base_color': transmission_color,
                'specularIOR': specularIOR,
                'specularRoughness': specularRoughness,
                'metalness' : metalness,
                "transmissionDispersion" : transmissionDispersion


            }

    # Define the JSON file path
    json_file_path = 'D:/luxcore_tmp/shaders.json'  # Update this path
    directory = os.path.dirname(json_file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Write all shader data to a single JSON file
    with open(json_file_path, 'w') as json_file:
        json.dump(all_shaders_data, json_file, indent=4)

    print(f'All shader data written to {json_file_path}')

def run ():
    print("Starting import all references")
    importAllReferences()
    print("Succes import all references")
    print("Starting renameNamespacesToRandom")
    renameNamespacesToRandom()
    print("Succes renameNamespacesToRandom")
    print("Starting redirectAiSurfaceShaderToSurfaceShader")
    redirectAiSurfaceShaderToSurfaceShader()
    print("Succes redirectAiSurfaceShaderToSurfaceShader")
    print ("Starting Export json")
    exportJson()
    print("Success export json")
run()
