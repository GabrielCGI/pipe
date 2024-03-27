import maya.cmds as cmds
import json
import os
import pymel.core as pm
import random
import string
import sys
import pymel.core as pm

import pymel.core as pm




import pymel.core as pm

def ensure_two_shaders():
    def create_or_get_temp_shader():
        """Create or return the temporary shader and its shading group."""
        if not pm.objExists('tempShader'):
            temp_shader = pm.shadingNode('lambert', asShader=True, name='tempShader')
            temp_shader_sg = pm.sets(renderable=True, noSurfaceShader=False, empty=True, name='tempShaderSG')
            pm.connectAttr(temp_shader + '.outColor', temp_shader_sg + '.surfaceShader', force=True)
        else:
            temp_shader = pm.PyNode('tempShader')
            temp_shader_sg = pm.PyNode('tempShaderSG')
        return temp_shader, temp_shader_sg

    def find_next_available_index(connections):
        """Find the next available index from connections."""
        indices = [int(str(c[0]).split('[')[-1][:-1]) for c in connections if c[0]]
        return max(indices) + 1 if indices else 0

    # Create or get the temporary shader and its shading group
    temp_shader, temp_shader_sg = create_or_get_temp_shader()

    # Get selected objects
    selected_objects = pm.ls(dag=True, type='mesh')

    for obj in selected_objects:
        # Get the original shading group
        shading_groups = pm.listConnections(obj, type='shadingEngine')
        if shading_groups:
            original_sg = shading_groups[0]

            # Assign the first face of the object to the temp shading group
            first_face = obj.faces[0]
            pm.sets(temp_shader_sg, forceElement=first_face)

            # Find the next available index for dagSetMembers in the original shading group
            connections = original_sg.dagSetMembers.listConnections(c=True, p=True)
            next_index = find_next_available_index(connections)

            # Create a new connection from the original shading group to the object
            pm.connectAttr(f'{obj}.instObjGroups[0].objectGroups[0]', f'{original_sg}.dagSetMembers[{next_index}]', force=True)

    # Delete the temporary shader and shading group
    pm.delete(temp_shader, temp_shader_sg)




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
        # Only rename the namespace if its length is greater than 5 characters
        if len(ns) > 5:
            # Generate a unique new namespace name
            newNs = generateUniqueName(renamedNamespaces)

            # Rename the namespace
            pm.namespace(rename=[ns, newNs])
            print(f"Renamed namespace from {ns} to {newNs}")

            # Keep track of the new namespace names to ensure uniqueness
            renamedNamespaces.add(newNs)
        else:
            print(f"Namespace {ns} not renamed because its length is not greater than 5 characters.")



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

def connect_aiRaySwitch_camera_to_shading_group():
    # Get all shading groups in the scene
    shading_groups = pm.ls(type='shadingEngine')

    for sg in shading_groups:
        # Find the shader connected to the surfaceShader input of the shading group
        connected_shaders = sg.surfaceShader.inputs()
        print(connected_shaders)

        if connected_shaders:
            shader = connected_shaders[0]

            # Check if the shader is of type aiRaySwitch
            if shader.nodeType() == 'aiRaySwitch':
                print("yo")
                # Get the shader connected to the .camera input of the aiRaySwitch shader
                camera_shader = shader.camera.inputs()

                if camera_shader:
                    # Connect the camera_shader to the surfaceShader input of the shading group
                    pm.connectAttr(camera_shader[0].outColor, sg.surfaceShader, force=True)

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
                pm.disconnectAttr(connection, sg.aiSurfaceShader)

                print(f"Redirected connection from {connection} to surfaceShader of {sg.name()}")

# Execute the function


def export_shaders_json():
    all_shaders_data = {}

    # Get all shading groups in the scene
    shading_groups = pm.ls(type='shadingEngine')

    for sg in shading_groups:
        # Get the shader connected to the surfaceShader attribute of the shading group
        shaders = sg.surfaceShader.listConnections()

        # Proceed if there's a connected shader and it's an aiStandardSurface
        if shaders and shaders[0].type() == 'aiStandardSurface':
            shader = shaders[0]

            # Initialize a dictionary to store attribute values or texture paths
            attrs = {}

            # List of shader attributes to check
            shader_attrs = ['transmission', 'transmissionColor', 'baseColor',
                            'specularIOR', 'specularRoughness', 'metalness',
                            'transmissionDispersion']

            for attr_name in shader_attrs:
                attr = getattr(shader, attr_name)

                # Check if the attribute has an input connection
                inputs = attr.listConnections(s=True, d=False)
                if inputs:
                    input_node = inputs[0]

                    # Check for file or aiImage nodes and fetch the texture path
                    if input_node.type() == 'file':
                        texture_path = input_node.fileTextureName.get()
                        attrs[attr_name] = texture_path
                    elif input_node.type() == 'aiImage':
                        texture_path = input_node.filename.get()
                        attrs[attr_name] = texture_path
                    else:
                        # If connected but not a texture node, fetch the attribute value
                        attrs[attr_name] = attr.get()
                else:
                    # If no input connection, fetch the attribute value
                    attrs[attr_name] = attr.get()

            # Update all_shaders_data with the fetched attributes or texture paths
            all_shaders_data[sg.name()] = attrs



    # Convert dictionary to JSON and print or save as needed


    # Define the JSON file path
    json_file_path = 'D:/luxcore_tmp/shaders.json'  # Update this path
    directory = os.path.dirname(json_file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Write all shader data to a single JSON file
    with open(json_file_path, 'w') as json_file:
        json.dump(all_shaders_data, json_file, indent=4)

    print(f'All shader data written to {json_file_path}')


# Call the function


def run ():
    confirm = cmds.confirmDialog(
        title='Confirm',
        message='This script will prepare the scene for caustic alembic export (save before !):\nContinue?',
        button=['Yes', 'No'],
        defaultButton='Yes',
        cancelButton='No',
        dismissString='No')

    if confirm == 'No':
        print("Operation aborted by the user.")
        return  # Abort script execution
    importAllReferences()
    print("Succes import all references")
    print("Starting renameNamespacesToRandom")
    renameNamespacesToRandom()
    print("Succes renameNamespacesToRandom")
    print("Starting redirectAiSurfaceShaderToSurfaceShader")
    redirectAiSurfaceShaderToSurfaceShader()
    connect_aiRaySwitch_camera_to_shading_group()
    print("Succes redirectAiSurfaceShaderToSurfaceShader")
    ensure_two_shaders()
    print("ensure two shader fix")
    print ("Starting Export json")
    export_shaders_json()
    print("Success export json")
