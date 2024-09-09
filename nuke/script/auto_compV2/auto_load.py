from imp import reload
from nukescripts import panels
import auto_compV2

reload(auto_compV2.AutoComp)
reload(auto_compV2.UnpackMode)
reload(auto_compV2.AutoCompFactory)
reload(auto_compV2.ShuffleMode)

panels.registerWidgetAsPanel("auto_compV2.AutoComp.AutoComp", 'AutoComp V2', 'illogic_studios.autocompV2')