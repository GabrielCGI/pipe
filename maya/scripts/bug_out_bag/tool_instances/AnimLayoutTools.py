from ..tool_models.MultipleActionTool import *
from importlib import reload
import traceback
import sys

try:
    import PrismInit
    PRISM_IMPORT = True
except:
    print("impossible de load PrismInit")
    
    PRISM_IMPORT = False



MODULES_SEARCH_PATH = ["R:/pipeline/pipe/prism", "R:/pipeline/pipe/maya/scripts"]
for module_path in MODULES_SEARCH_PATH:
    if not module_path in sys.path:
        sys.path.append(module_path)



class AnimLayoutTools(MultipleActionTool):
    def __init__(self):
        self.core = PrismInit.pcore if PRISM_IMPORT else None
        actions = {
            "openReferenceUpdater": {
                "text": "Open Reference Updater",
                "action": self.startUI,
                "row": 0
            },
            "openControlerSplitingVariant": {
                "text": "Controler Split Variant",
                "action": self.startControler,
                "row": 0
            },
        }
        tooltip = "open Reference Updater"
        super().__init__(
            name="Anim Layout Tools",
            pref_name="anim_layout_tools",
            actions=actions, stretch=1, tooltip=tooltip)
    
    def startControler(self):
        import split_variants_rig as svr
        svr.controler(self.core)

    def startUI(self):
        try:
            import referenceUpdater as refUp
            reload(refUp)
        except:
            traceback.print_exc()
            print("impossible de load refUpdater")
            return

        try:
            path = self.core.getCurrentFileName()
            
            self.win = refUp.mainUI(self, "Maya", path, self.core.projectPath, False)
            self.win.show()
        except Exception as e:
            print(e)