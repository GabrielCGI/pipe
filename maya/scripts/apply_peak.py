import maya.cmds as cmds

def apply_small_peak_texture_deformer(strength=1.0, tex_value=0.05):
    """
    Apply a small 'peak' style texture deformer to the selected mesh.
    Wrapped in a single undo chunk so everything undoes in one step.
    """
    # Start undo chunk
    cmds.undoInfo(openChunk=True)
    created = []

    try:
        # Get selected shapes
        sel = cmds.ls(sl=True, dag=True, shapes=True) or []
        if not sel:
            cmds.warning("Select at least one mesh object.")
            return

        for shape in sel:
            # Create the texture deformer on this shape
            deformer, handle = cmds.textureDeformer(
                shape,
                envelope=1,
                strength=strength,
                offset=0,
                vectorStrength=(1, 1, 1),
                vectorOffset=(0, 0, 0),
                vectorSpace="Object",
                direction="Handle",
                pointSpace="UV",
                exclusive=""
            )

            # Match your echo commands
            cmds.setAttr(deformer + ".direction", 0)
            cmds.setAttr(
                deformer + ".texture",
                tex_value, tex_value, tex_value,
                type="double3"
            )

            # Optional: move the handle a bit in Y to make a visible "peak"
            cmds.setAttr(handle + ".ty", strength)

            created.append((deformer, handle))

        print("Created texture deformers:", created)
        cmds.select(sel)
        return created

    finally:
        # Close undo chunk even if something errors
        cmds.undoInfo(closeChunk=True)

