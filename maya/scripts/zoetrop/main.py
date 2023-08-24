from zoetrop_app import ui
from zoetrop_app import logic

import importlib
importlib.reload(ui)
importlib.reload(logic)

try:
    zoetrop_ui.close()
except:
    pass
zoetrop_ui = ui.CustomUI()
zoetrop_ui.show()
