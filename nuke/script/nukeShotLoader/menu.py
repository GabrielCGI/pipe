"""Registers the "Shot Loader" menu in Nuke.

Loaded automatically once this folder is on the plugin path:
    nuke.pluginAddPath(r"R:/pipeline/pipe/nuke/script/nukeShotLoader")
"""

import os
import sys
import traceback

import nuke

# v1 precomp scripts import `module_precomp` flat, so src/ must be importable.
_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

try:
    from src.precomp import commands, watcher
    from src.ui.main_window import show_shot_asset_loader, show_shot_render_manager

    _menu = nuke.menu("Nuke").addMenu("Shot Loader")
    _menu.addCommand("Shot Asset Loader", show_shot_asset_loader, "Ctrl+Alt+A")
    _menu.addCommand("Shot Render Manager", show_shot_render_manager, "Ctrl+Alt+W")
    _menu.addSeparator()
    _menu.addCommand("Precomp/Insert Precomp", commands.insert_precomp)
    _menu.addCommand("Precomp/Insert Compo Write", commands.insert_compo_write)
    _menu.addCommand("Precomp/Refresh Precomps", commands.refresh, "Ctrl+Alt+R")
    _menu.addCommand("Precomp/Upgrade Precomps", commands.upgrade)
    watcher.install()
    # Prism tab of the Compo / Precomp Writes of each script opened -> the Shot Loader's.
    nuke.addOnScriptLoad(commands.upgrade_prism_tabs)
    nuke.addKnobChanged(commands.lock_version_display, nodeClass="Write")
    print("[nukeShotLoader] Shot Loader menu added")
except Exception as e:
    nuke.message(f"Error loading Shot Asset Loader menu: {e}")
    print(f"[nukeShotLoader] Error: {e}")
    traceback.print_exc()
