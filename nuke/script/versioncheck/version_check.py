from pathlib import Path
import json
import nuke # type: ignore
import sys
import os


try:
    from PySide6 import QtWidgets
except ImportError:
    try:
        from PySide2 import QtWidgets # type: ignore
    except ImportError:
        sys.exit(1)


PROJECT_CONFIG = os.path.join(os.path.dirname(__file__), 'projects_config.json')


def checkVersion(project_config=PROJECT_CONFIG):
    with open(project_config, 'r') as config_f:
        pc_data = json.load(config_f)

    script_path = Path(nuke.root().name())
    if len(script_path.parts) < 2:
        return
    script_prod_name = script_path.parts[1]
    
    productions_data = pc_data.get("productions", [])
    for p_data in productions_data:
        prod_name = p_data['project_name']
        if prod_name != script_prod_name:
            continue
        allowed_version = p_data['allowed_version']
        resolution_mismatch = p_data.get('bypass_mismatch', False)
        if resolution_mismatch:
            mismatch_list = p_data.get("mismatch_list", [])
            close_mismatch(mismatch_list)
        if nuke.NUKE_VERSION_STRING not in allowed_version:
            close_unwanted_popups()
            nuke.scriptClose()
            msg = (
                "Cannot open this scene with current "
                f"Nuke version ({nuke.NUKE_VERSION_STRING})\n"
                "Expected version:\n"
            ) + "\n".join(allowed_version)
            nuke.message(msg)
            print(msg)


def close_mismatch(mismatch_list):
    app = QtWidgets.QApplication.instance()
    if app is None:
        return
    for widget in app.topLevelWidgets():
        if isinstance(widget, QtWidgets.QMessageBox):
            title = widget.windowTitle()
            if title in mismatch_list:
                widget.done(0)


def close_unwanted_popups():
    app = QtWidgets.QApplication.instance()
    if app is None:
        return
    for widget in app.topLevelWidgets():
        if isinstance(widget, QtWidgets.QMessageBox):
            title = widget.windowTitle()
            if title in ["Resolution mismatch", 'FPS mismatch', 'Framerange mismatch']:
                widget.done(0)


def load_callback():
    on_script_load_cbs = nuke.callbacks.onScriptLoads['Root']
    for i in range(len(on_script_load_cbs)-1, -1, -1):
        cb_function = on_script_load_cbs[i][0]
        if cb_function.__name__ == "checkVersion":
            nuke.removeOnScriptLoad(cb_function)

    nuke.addOnScriptLoad(checkVersion)
