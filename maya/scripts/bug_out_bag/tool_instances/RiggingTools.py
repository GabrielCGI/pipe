from ..tool_models.MultipleActionTool import *
from importlib import reload
import maya.cmds as cmds
import sys

try:
    import PrismInit
    PRISM_IMPORT = True
except:
    print("impossible de load PrismInit")
    
    PRISM_IMPORT = False



MODULES_SEARCH_PATH = ["R:/pipeline/pipe/maya/scripts"]
for module_path in MODULES_SEARCH_PATH:
    if not module_path in sys.path:
        sys.path.append(module_path)



class RiggingTools(MultipleActionTool):
    def __init__(self):
        self.core = PrismInit.pcore if PRISM_IMPORT else None
        actions = {
            "openUISplitVariant": {
                "text": "UI split Variant",
                "action": self.startUISplitVariant,
                "row": 0
            },
        }
        tooltip = "open Reference Updater"
        super().__init__(
            name="Rigging Tools",
            pref_name="rigging_tools",
            actions=actions, stretch=1, tooltip=tooltip)

    def startUISplitVariant(self):
        import split_variants_rig as svr
        scene_path = self.core.getCurrentFileName()
        if not 'Rigging\\Rigging' in scene_path:
            return
        
        spliter_variant = svr.main(self.core, scene_path)
        spliter_variant.passPrePublish()