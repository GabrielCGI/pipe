import importlib
from . import autoconnect_ui

def main(enable_debug=False):
    if enable_debug:
        from . import debug
        importlib.reload(debug)
        # Also need to enable it in debug module
        debug.debug()
    importlib.reload(autoconnect_ui)
    autoconnect_ui.showUI()