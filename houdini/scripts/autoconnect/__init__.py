import importlib
from . import autoconnect_ui


def reload_all_modules():
    from . import auto
    from . import houdinilog
    from . import map
    from . import qt
    from . import ressource
    from . import shader
    importlib.reload(auto)
    importlib.reload(houdinilog)
    importlib.reload(map)
    importlib.reload(qt)
    importlib.reload(ressource)
    importlib.reload(shader)


def main(enable_debug=False, reload_all=False):
    if enable_debug:
        from . import debug
        importlib.reload(debug)
        # Also need to enable it in debug module
        debug.debug()
    if reload_all:
        reload_all_modules()
    importlib.reload(autoconnect_ui)
    autoconnect_ui.showUI()