import maya.cmds as cmds
import pymel.core as pm
def run_edge():
    # Ensure you have a face selection
    selection = cmds.ls(selection=True)
    print(selection)


    # Check if there is a selection and it's a polygon face
    if selection:
        mesh = selection[0].split('.')[0]  # Get the mesh from the first selected face

        # Enable color export on the mesh
        cmds.setAttr(mesh + '.aiExportColors', 1)

        # Check if the color set "border" already exists
        existing_color_sets = cmds.polyColorSet(mesh, query=True, allColorSets=True) or []
        if 'border' not in existing_color_sets:
            # Create a new color set named "border"
            cmds.polyColorSet(mesh, create=True,rpt="RGB", colorSet='border')
            cmds.polyColorSet(mesh, currentColorSet=True, colorSet='border')
            cmds.polyColorPerVertex(mesh + '.vtx[*]', rgb=(0, 0, 0), colorDisplayOption=True)

        # Set "border" as the current color set
        cmds.polyColorSet(mesh, currentColorSet=True, colorSet='border')
        # Set the selected face to white
        cmds.polyColorPerVertex(selection, rgb=(1, 1, 1), colorDisplayOption=True)
    else:
        print("Please select a polygon face to proceed.")

def lamberificator(first_item):
    if "." in first_item:  # Checks if the selection includes components
        shape_name = first_item.split(".")[0]  # Extracts the object name before the first dot
        shape = pm.ls(shape_name)[0].getShape()  # Use PyMEL to get the shape node
        print(shape)
    elif cmds.objectType(first_item, isType='transform'):
        shape = pm.ls(first_item)[0].getShape()  # Directly get shape node if the transform was selected
        print(shape)
    else:
        pm.warning("Selected item is neither a mesh component nor a transform.")
        return

    # List all shading groups connected to the mesh
    shading_groups = pm.listConnections(shape, type='shadingEngine')
    print(shading_groups)
    if not shading_groups:
        pm.warning("No shading groups found connected to the selected mesh.")
        return

    # Process each shading group
    for sg in shading_groups:
        # Check the current shader connected to surfaceShader input
        current_shader = pm.listConnections(sg.surfaceShader, source=True, destination=False)
        print(current_shader)
        if current_shader:
            shader_type = pm.nodeType(current_shader[0])
            # Check if the shader is not a blinn or lambert
            if shader_type not in ['blinn', 'lambert']:
                print("yeaj")
                # Create aiStandardSurface shader if not already connected
                pm.connectAttr(current_shader[0].outColor, sg.aiSurfaceShader, force=True)

                # Connect lambert1 to surfaceShader as well
                lambert1 = pm.PyNode('lambert1')
                pm.connectAttr(lambert1.outColor, sg.surfaceShader, force=True)

def run_color():
    # Ensure you have a selection
    selection = cmds.ls(selection=True)
    if not selection:
        pm.warning("No selection made.")
        return
    print(selection[0])
    lamberificator(selection[0])

    if 'f' in selection[0]:  # Face components are selected
        target = selection[0].split('.')[0]
    else:  # Entire mesh is selected
        target = selection[0]

    # Enable color export on the mesh
    cmds.setAttr(target + '.aiExportColors', 1)

    # Check if the color set "Cd" already exists
    existing_color_sets = cmds.polyColorSet(target, query=True, allColorSets=True) or []
    if 'Cd' not in existing_color_sets:
        # Create a new color set named "Cd"
        cmds.polyColorSet(target, create=True, rpt="RGB", colorSet='Cd')

    # Set "Cd" as the current color set
    cmds.polyColorSet(target, currentColorSet=True, colorSet='Cd')

    # Ask the user to select a color
    color = cmds.colorEditor()
    if cmds.colorEditor(query=True, result=True):
        rgb = cmds.colorEditor(query=True, rgb=True)
        # Set the selected face or entire mesh to the chosen color
        cmds.polyColorPerVertex(selection if 'f' in selection[0] else target + '.vtx[*]', rgb=rgb, colorDisplayOption=True)
    else:
        print("Color selection cancelled.")
