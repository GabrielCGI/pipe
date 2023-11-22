from ..tool_models.ActionTool import *


class Orig(ActionTool):
    def __init__(self):
        # TODO Modify fields as you want (pref_name should be unique)
        super().__init__(name="oRig Tool",pref_name="oRig",
                         description="Create an orig and freeze transform", button_text="Run", tooltip="Not working if any reference detected")

    def _action(self):
        # Open an undo chunk
        pm.undoInfo(openChunk=True)

        try:
            selected_objects = pm.ls(selection=True)

            for obj in selected_objects:
                reference = False
                # Check if the object itself or any of its children is a referenced node
                if obj.isReferenced() or any(child.isReferenced() for child in pm.listRelatives(obj, allDescendents=True)):
                    pm.warning(f"Object {obj} or its children are referenced. Skipping transformation freeze.")
                    reference = True

                short_name = obj.split('|')[-1]
                orig_group = pm.group(empty=True, name=f'{short_name}_orig')
                pm.matchTransform(orig_group, obj)

                # Parent the group to the object's current parent
                parent = pm.listRelatives(obj, parent=True)
                if parent:
                    pm.parent(orig_group, parent[0])

                # Parent the object under the orig group
                pm.parent(obj, orig_group)

                # Freeze the transformation of the object
                if not reference:
                    pm.makeIdentity(obj, apply=True, translate=True, rotate=True, scale=True, normal=False)

        finally:
            # Close the undo chunk
            pm.undoInfo(closeChunk=True)
