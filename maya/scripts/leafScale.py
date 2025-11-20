import maya.cmds as cmds

def root_select():
    pattern = "leaves*:ctrl_world"

    # Find matching objects
    matches = cmds.ls(pattern) or []

    # Select them if found
    if matches:
        cmds.select(matches, r=True)
        print("Selected objects:")
        for m in matches:
            print("  -", m)
    else:
        cmds.warning("No objects found matching: {}".format(pattern))
def run():
    # Patterns to match
    patterns = [
        "leaves*:ctrl_walk",
        "leaves*:*tigeStart"
    ]

    # Collect matches
    matched_objects = []
    for p in patterns:
        matches = cmds.ls(p) or []
        matched_objects.extend(matches)

    # Select matched objects
    if matched_objects:
        cmds.select(matched_objects, r=True)
    else:
        cmds.warning("No objects found for the given patterns.")
        matched_objects = []


    # ---- Check scale values ----
    scaled_objects = []

    for obj in matched_objects:
        sx = cmds.getAttr(obj + ".scaleX")
        sy = cmds.getAttr(obj + ".scaleY")
        sz = cmds.getAttr(obj + ".scaleZ")

        if not (abs(sx - 1) < 1e-6 and abs(sy - 1) < 1e-6 and abs(sz - 1) < 1e-6):
            scaled_objects.append(obj)


    # ---- Popup if scaled objects detected ----
    if scaled_objects:
        count = len(scaled_objects)
        
        # Popup message with ONLY the count
        msg = "Scaled detected on {} object(s).\nReset scale to 1?".format(count)

        result = cmds.confirmDialog(
            title="Scale Warning",
            message=msg,
            button=["Reset", "Cancel"],
            defaultButton="Reset",
            cancelButton="Cancel",
            dismissString="Cancel"
        )

        # User confirmed → reset
        if result == "Reset":
            for obj in scaled_objects:
                cmds.setAttr(obj + ".scaleX", 1)
                cmds.setAttr(obj + ".scaleY", 1)
                cmds.setAttr(obj + ".scaleZ", 1)

            print("\nScales reset to 1 for:")
            for o in scaled_objects:
                print("  -", o)
        else:
            print("User cancelled. No scale reset performed.")

    else:
        print("All matched objects have default scale.")
