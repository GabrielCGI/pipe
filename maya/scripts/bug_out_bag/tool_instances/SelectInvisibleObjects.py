from ..tool_models.ActionTool import *

from common.utils import *

class SelectInvisibleObjects(ActionTool):
    def __init__(self):
        super().__init__(name="Select Inivisble Objects", pref_name="select_inivisble_objects",
                         description="Selects the invisible objects in the scene", button_text="Run")

    def _action(self):
        # Get all transform nodes in the scene
        all_transforms = pm.ls(type='transform')
        
        # Filter out nodes that are not visible
        invisible_objects = [node for node in all_transforms if not node.visibility.get()]
        
        # Select all the invisible objects
        pm.select(invisible_objects)