import importlib
from . import autoconnect_ui
from . import debug

def main(enable_debug=False):
    if enable_debug:
        # Also need to enable it in debug module
        debug.debug()
    importlib.reload(autoconnect_ui)
    importlib.reload(debug)
    autoconnect_ui.showUI()