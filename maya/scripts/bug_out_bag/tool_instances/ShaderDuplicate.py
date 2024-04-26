from ..tool_models.ActionTool import *
from common.utils import *


class ShaderDuplicate(ActionTool):
    def __init__(self):
        super().__init__(name="Duplicate shader ",pref_name="duplicate_shader",
                         description="Duplicate selected shaders (keep colorspace)", button_text="Duplicate")


    def _action(self):
        # Get selected nodes
        selected_nodes = pm.selected()

        # Duplicate the network
        duplicated_nodes = pm.duplicate(selected_nodes, un=True)

        # Mapping original to duplicated nodes
        original_to_duplicate = {original: duplicate for original, duplicate in zip(selected_nodes, duplicated_nodes)}

        # Ensure color space is preserved for textures
        for original, duplicate in original_to_duplicate.items():
            if isinstance(original, pm.nt.File):
                # Copy color space from original to duplicate
                try:
                    color_space = original.cs.get()
                    duplicate.cs.set(color_space)
                    print("Succes %s set to  %s"%(original, original.cs.get() ))
                except:
                    print("CS update fail" + original)
                    pass


        return duplicated_nodes
