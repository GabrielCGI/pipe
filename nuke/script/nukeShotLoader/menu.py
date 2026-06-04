"""
Nuke Menu Integration for Shot Asset Loader

Installation:
1. Copy the entire nukeGetShotAssets folder to a location accessible by Nuke
2. Add this to your ~/.nuke/menu.py or init.py:

   import sys
   sys.path.append("r:/devMathieu/nukeGetShotsAssets")
   import menu

This will add "Shot Asset Loader" to the Custom menu in Nuke.
"""

import nuke
import sys
import os

# Add src to path
current_dir = os.path.dirname(__file__)
src_dir = os.path.join(current_dir, "src")

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import the UI function
try:
    from src.ui_loader_simple import show_shot_asset_loader

    # Add to Shot Loader menu (or create it if it doesn't exist)
    toolbar = nuke.menu("Nuke")
    custom_menu = toolbar.addMenu("Shot Loader")

    # Add the Shot Asset Loader menu item
    custom_menu.addCommand(
        "Shot Asset Loader",
        show_shot_asset_loader,
        "Ctrl+Alt+A"  # Keyboard shortcut
    )

    print("[nukeGetShotAssets] Shot Asset Loader menu added successfully")

except Exception as e:
    nuke.message(f"Error loading Shot Asset Loader menu: {e}")
    print(f"[nukeGetShotAssets] Error: {e}")
    import traceback
    traceback.print_exc()
