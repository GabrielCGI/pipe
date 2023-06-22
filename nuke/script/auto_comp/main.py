import importlib
from common import utils

utils.unload_packages(silent=True, package="auto_comp")
importlib.import_module("auto_comp")
from auto_comp.AutoComp import AutoComp
try:
    auto_comp_pane.destroy()
except:
    pass
from nukescripts import panels
auto_comp_pane = nuke.getPaneFor('Properties.1')
panels.registerWidgetAsPanel("AutoComp", 'AutoComp', 'illogic_studios.auto_comp', True).addToPane(auto_comp_pane)
auto_comp_pane.show()
