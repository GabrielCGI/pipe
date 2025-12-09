from imp import reload
from nukescripts import panels
import auto_comp

reload(auto_comp.AutoComp)
reload(auto_comp.UnpackMode)

panels.registerWidgetAsPanel("auto_comp.AutoComp.AutoComp", 'AutoComp', 'illogic_studios.autocomp')