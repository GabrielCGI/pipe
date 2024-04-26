def run():
    # Ensure you have a face selection
    selection = pm.selected()

    # Check if there is a selection and it's a polygon face
    if selection and isinstance(selection[0], pm.general.MeshFace):
        mesh = selection[0].node()
        mesh.aiExportColors.set(1)

        # Check if the color set "border" already exists
        existing_color_sets = pm.polyColorSet(mesh, query=True, allColorSets=True) or []
        if 'border' not in existing_color_sets:
            # Create a new color set named "border"
            pm.polyColorSet(mesh, create=True, colorSet='border')

        # Set "border" as the current color set
        pm.polyColorSet(mesh, currentColorSet=True, colorSet='border')

        # Set the selected face to white
        pm.polyColorPerVertex(selection, rgb=(1, 1, 1), colorDisplayOption=True)

    else:
        print("Please select a polygon face to proceed.")
