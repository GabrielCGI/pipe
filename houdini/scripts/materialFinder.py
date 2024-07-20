# Copyright © 2024 Valentin Dornel

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Script created by Illogic Studios
v1.0 (tested on H20.0.688): 2024-07-10

Description :
Get materials from current selections to display in the Network View.
(similar too Maya function: graph material from selection )

We can put this script in a shelf button like this:
import sys
sys.path.append(r"R:\pipeline\pipe\houdini\scripts")
import materialFinder
materialFinder.run()
"""

__author__ = "Gabriel Grapperon"
__credits__ = ["ValDo Dornel"]
__license__ = "MIT License 2024"
__version__ = "1.0"



import hou
from pxr import UsdShade
def find_lop_network(node):
    while node:
        if node.type().name() == 'lopnet':
            return node
        node = node.parent()
    return None



def run():
    pane = hou.ui.findPaneTab('panetab8')
    network = pane.pwd()

    lop_network = find_lop_network(network)
    if lop_network:
        print(f"Found LOP network: {lop_network.path()}")
    else:
        print("No LOP network found. Defaulting to stage")
        lop_network=hou.node("/stage")
    print(lop_network)
    selection = lop_network.selection()[0]
    display_node= lop_network.displayNode().path()


    stage = hou.node(display_node).stage()

    selected_prim = stage.GetPrimAtPath(selection)
    print(selected_prim)
    #props = selected_prim.GetPropertyNames()
    type = selected_prim.GetTypeName()

    if type == "Material":
        material_path = selected_prim
    else:
        bound_material, _= UsdShade.MaterialBindingAPI(selected_prim).ComputeBoundMaterial()
        material_path = bound_material.GetPrim()



    # Get the currently selected primitives
    material_node_id = material_path.GetMetadata("customData")["HoudiniPrimEditorNodes"][0]
    mat_node = hou.nodeBySessionId(material_node_id)

    desktop = hou.ui.curDesktop()
    network_editor = desktop.paneTabOfType(hou.paneTabType.NetworkEditor)
    network_editor.cd(mat_node.parent().path())
    network_editor.setCurrentNode(mat_node, True)
    network_editor.homeToSelection()
