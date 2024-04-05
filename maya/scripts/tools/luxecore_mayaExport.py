import maya.cmds as cmds
import json
import os
import pymel.core as pm
import random
import string
import sys
import pymel.core as pm
import hashlib
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
    def generateHashedName(name, existingNames):
        # Ensure the hash starts with a letter ('n' in this case) for Maya compatibility
        # Generate a consistent hash from the namespace name
        hash_object = hashlib.sha256(name.encode())  # Using sha256 for better distribution
        hex_dig = hash_object.hexdigest()
        # We start with 'n' and then take 4 characters from the hash, adjusting as needed
        baseName = 'n' + hex_dig[:4]
        newName = baseName
        i = 1  # Start counting from 1 for any necessary suffixes
        # Ensure uniqueness in the scene
        while newName in existingNames or pm.namespace(exists=newName):
            newName = 'n' + hex_dig[i:i+4]  # Shift the window for the next 4 chars of the hash
            i += 1
        return newName

    # Get all namespaces except for the root and UI namespaces, which cannot be renamed
    allNamespaces = [ns for ns in pm.namespaceInfo(listOnlyNamespaces=True, recurse=True) if ns not in ['UI', 'shared']]

    # Sort namespaces by depth, so we rename children before parents to avoid conflicts
    allNamespaces.sort(key=lambda x: x.count(':'), reverse=True)

    renamedNamespaces = set()

    for ns in allNamespaces:
        # Only rename the namespace if its length is greater than 5 characters
        if len(ns) > 5:
            # Generate a consistent new namespace name
            newNs = generateHashedName(ns, renamedNamespaces)

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
def delete_invisible_objects():
    """
    Deletes all invisible objects in the scene. This function iterates through all transform nodes
    and deletes those where the visibility attribute is set to False.
    """
    # List all transform nodes in the scene
    all_transforms = pm.ls(type='transform')

    # Filter out transforms that are not visible
    invisible_transforms = [transform for transform in all_transforms if not transform.visibility.get()]

    # Delete the invisible transforms
    if invisible_transforms:
        pm.delete(invisible_transforms)
        print(f"Deleted {len(invisible_transforms)} invisible objects.")
    else:
        print("No invisible objects found to delete.")

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

def apply_polySmooth_based_on_conditions():
    """
    Applies a polySmooth to meshes based on specific conditions:
    - If aiSubdivType is set to 1 (Catmull-Clark) and aiSubdivIterations is greater than 0.
    - Or if the mesh has Smooth Mesh Preview activated.
    The polySmooth resolution matches aiSubdivIterations up to a maximum of 2, or is set to 2 if using Smooth Mesh Preview.
    """
    # Iterate through all mesh nodes in the scene
    for mesh in pm.ls(type='mesh'):
        # Ensure the mesh has a transform node parent
        transform_node = mesh.getParent()

        # Initialize variables
        apply_smooth = False
        smooth_level = 0

        # Check for Arnold subdivision attributes
        if pm.attributeQuery('aiSubdivType', node=mesh, exists=True) and pm.attributeQuery('aiSubdivIterations', node=mesh, exists=True):
            if mesh.aiSubdivType.get() == 1 and mesh.aiSubdivIterations.get() > 0:
                apply_smooth = True
                smooth_level = min(mesh.aiSubdivIterations.get(), 2)

        # Check for Smooth Mesh Preview activation
        if transform_node.displaySmoothMesh.get() != 0:
            apply_smooth = True
            smooth_level = 2

        # Apply polySmooth if conditions are met
        if apply_smooth:
            transform_node.displaySmoothMesh.set(0)
            pm.polySmooth(mesh, divisions=smooth_level, mth=0, sdt=2, ovb=1, ofb=3, ofc=0, ost=1, ocr=0, dv=smooth_level, c=1, kb=1, ksb=1, khe=0, kt=1, kmb=1, suv=1, peh=0, sl=1, dpe=1, ps=0.1, ro=1, ch=1)
            print(f"Applied polySmooth to {transform_node} with division level {smooth_level}.")

def export_shaders_json():
    all_shaders_data = {}

    # Get all shading groups in the scene
    shading_groups = pm.ls(type='shadingEngine')

    for sg in shading_groups:
        # Get the shader connected to the surfaceShader attribute of the shading group
        connections = sg.surfaceShader.listConnections(plugs=True)

        shader = None
        for conn in connections:
            # Check if the connection is from an aiTraceSet node
            if conn.node().type() == 'aiTraceSet':
                # Get the shader connected to the passthrough input of the aiTraceSet
                passthrough_connections = conn.node().passthrough.listConnections()
                if passthrough_connections:
                    shader = passthrough_connections[0]
                    break
            else:
                # Direct connection from an aiStandardSurface shader
                if conn.node().type() == 'aiStandardSurface':
                    shader = conn.node()
                    break

        # Proceed if a shader has been identified
        if shader:
            # Initialize a dictionary to store attribute values or texture paths
            attrs = {}
            # List of shader attributes to check
            shader_attrs = ['transmission', 'transmissionColor', 'baseColor',
                            'specularIOR', 'specularRoughness', 'metalness',
                            'transmissionDispersion']

            for attr_name in shader_attrs:
                attr = getattr(shader, attr_name)
                attrs[attr_name] = attr.get()

                # Check if the attribute has an input connection
                inputs = attr.listConnections(s=True, d=False)
                if inputs:
                    input_node = inputs[0]

                    # Special handling for aiRaySwitch connected to transmissionColor
                    if attr_name == 'transmissionColor' and input_node.type() == 'aiRaySwitch':
                        # Get the connection from the "camera" input of the aiRaySwitch
                        camera_input = input_node.camera.listConnections(s=True, d=False)
                        if camera_input:
                            # Connect the camera input to the transmissionColor of the aiStandardSurface
                            camera_input[0].outColor.connect(shader.transmissionColor, f=True)

                            # Update the attrs dictionary after reconnecting
                            attrs[attr_name] = shader.transmissionColor.get()
                            continue  # Skip the rest of the loop for this attribute

                    # Check for file or aiImage nodes and fetch the texture path
                    if input_node.type() == 'file' or input_node.type() == 'aiImage':
                        texture_path = input_node.fileTextureName.get() if input_node.type() == 'file' else input_node.filename.get()
                        attrs[attr_name + '_texture'] = texture_path  # Store texture path under attributeName_texture
                    else:
                        # For non-texture connections, store the name of the connected node
                        attrs[attr_name + '_connection'] = input_node.name()

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
    print("delete invisible")
    delete_invisible_objects()
    print("Apply smooth")
    apply_polySmooth_based_on_conditions()
    print("Starting redirectAiSurfaceShaderToSurfaceShader")
    redirectAiSurfaceShaderToSurfaceShader()
    connect_aiRaySwitch_camera_to_shading_group()
    print("Succes redirectAiSurfaceShaderToSurfaceShader")
    ensure_two_shaders()
    print("ensure two shader fix")
    print ("Starting Export json")
    export_shaders_json()
    print("Success export json")
