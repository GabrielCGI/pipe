from ..tool_models.MultipleActionTool import *


class IsolateTool(MultipleActionTool):
    def __init__(self):
        actions = {
            "Isolate": {
                "text": "Isolate",
                "action": self.__isolate_object,
                "row": 0
            },
            "Show": {
                "text": "Show all",
                "action": self.__revert_isolation,
                "row": 0
            }
        }
        tooltip = "Isolate the selection"
        super().__init__(name="Isolate", pref_name="isolate_tool", actions=actions, stretch=1, tooltip=tooltip)

    def __isolate_object(self):
        # Get all transform nodes
        all_transforms = pm.ls(type='transform')

        # Get selected objects
        selected_objects = pm.selected()

        # Set non-selected shape transforms to Template
        for transform in all_transforms:
            if transform not in selected_objects:
                for shape in transform.getShapes():
                    if shape and shape.nodeType() == 'mesh':
                        pm.setAttr(transform + '.template', True)
            else:
                pm.setAttr(transform + '.template', False)

    def __revert_isolation(self):
        # Get all shape nodes
        all_transforms = pm.ls(type='transform')

        # Revert Template attribute to off
        for transform in all_transforms:
            pm.setAttr(transform + '.template', False)
