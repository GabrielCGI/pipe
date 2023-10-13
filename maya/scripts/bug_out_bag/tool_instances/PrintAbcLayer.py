from ..tool_models.ActionTool import *

from common.utils import *

class PrintAbcLayer(ActionTool):
    def __init__(self):
        super().__init__(name="Print Abc Layer", pref_name="print_abc_layer",
                         description="Print .abc layers of all selected stand-ins", button_text="Run")

    def _action(self):
        # Get all selected nodes
        sel = pm.selected()

        for node in sel:
            # Check if the node has the attribute 'abc_layers'
            if node.hasAttr('abc_layers'):
                abc_layers = node.abc_layers.get()
                print(f"\nStand-in: {node}\nABC Layer: {abc_layers}")

