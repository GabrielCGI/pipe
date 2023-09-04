from zoetrop_app import ui


import importlib
importlib.reload(ui)


try:
    zoetrop_ui.close()
except:
    pass
zoetrop_ui = ui.CustomUI()
zoetrop_ui.show()
