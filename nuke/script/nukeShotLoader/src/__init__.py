"""
nukeGetShotAssets
A Nuke tool for loading shot assets from Prism Pipeline.
"""

__version__ = "1.0.0"
__author__ = "Pipeline Team"

from .config import Config
from .prism_scanner import PrismScanner
from .asset_discoverer import AssetDiscoverer
from .positioning_manager import PositioningManager
from .nuke_node_builder import NukeNodeBuilder
from .stamps_integration import StampsIntegration, get_stamps_integration
from .ui_loader_simple import ShotAssetLoaderWindow, show_shot_asset_loader

__all__ = [
    "Config",
    "PrismScanner",
    "AssetDiscoverer",
    "PositioningManager",
    "NukeNodeBuilder",
    "StampsIntegration",
    "get_stamps_integration",
    "ShotAssetLoaderWindow",
    "show_shot_asset_loader",
]
