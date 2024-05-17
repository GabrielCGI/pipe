from ..tool_models.MultipleActionTool import *


class DisplayColor(MultipleActionTool):

    def __init__(self):
        actions = {
            "On": {
                "text": "On",
                "action": self.__on,
                "row": 0
            },
            "Off": {
                "text": "Off",
                "action": self.__off,
                "row": 0
            },

        }
        super().__init__(name="Display Color (sellection)", pref_name="displaycolor_tool",
                         actions=actions, stretch=1)



    def __off(self):
        # Get all selected objects
        selected_objects = pm.ls(selection=True, long=True)

        for obj in selected_objects:
            # Get shapes of the object and all its children recursively
            all_shapes = pm.listRelatives(obj, allDescendents=True, type='shape', fullPath=True) + pm.listRelatives(obj, shapes=True, fullPath=True)

            # Set the .displayColors attribute to off for each shape
            for shape in all_shapes:
                if pm.objExists(shape + ".displayColors"):
                    pm.setAttr(shape + ".displayColors", False)

    def __on(self):
        # Get all selected objects
        selected_objects = pm.ls(selection=True, long=True)

        for obj in selected_objects:
            # Get shapes of the object and all its children recursively
            all_shapes = pm.listRelatives(obj, allDescendents=True, type='shape', fullPath=True) + pm.listRelatives(obj, shapes=True, fullPath=True)

            # Set the .displayColors attribute to off for each shape
            for shape in all_shapes:
                if pm.objExists(shape + ".displayColors"):
                    pm.setAttr(shape + ".displayColors", True)
