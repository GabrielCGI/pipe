"""
Configuration module for nukeGetShotAssets
Contains all constants, paths, colors, and layout settings
"""

import os


class Config:
    """Centralized configuration for the Shot Asset Loader"""

    # ==================== PROJECT PATHS ====================
    DEFAULT_PROJECT_ROOT = r"I:\McDonald_2511"
    SHOTS_PATH = "03_Production/Shots"
    PIPELINE_PATH = "00_Pipeline"
    PIPELINE_JSON = "pipeline.json"
    SHOTINFO_JSON = "Shotinfo/shotInfo.json"

    # ==================== UI ASSETS ====================
    LOGO_PATH = r"R:/logos/logo.png"
    LOGO_OPACITY = 0.25

    # ==================== ASSET PATHS TEMPLATES ====================
    # Relative to shot folder
    PLATES_PATH = "Renders/external"
    RENDERS_3D_PATH = "Renders/3dRender"
    RENDERS_2D_PATH = "Renders/2dRender"
    CAMERA_PATH = "Export"

    # ==================== VERSION DETECTION ====================
    VERSION_PATTERN = r"v(\d{3,4})"  # Matches v001, v010, v0001, etc.

    # Folders to ignore when scanning versions
    IGNORE_VERSION_SUFFIXES = ["(mp4)", "(mov)", "(preview)", "_thumbs", "Thumbs.db"]

    # ==================== NODE GRAPH LAYOUT ====================
    NODE_SPACING_X = 200

    # Grid layout for reads inside an asset-type backdrop. Reads are placed in
    # rows of READS_PER_ROW columns and wrap to the next row beyond that.
    READS_PER_ROW = 10
    READ_COL_SPACING = 360   # x stride between consecutive reads in the same row
    READ_ROW_HEIGHT = 300    # y stride between read rows (room for anchor + wired stamp)

    # Backdrop positioning
    BACKDROP_PADDING = 150  # Increased for better readability with stamps

    # Starting position for first node
    START_X = 0
    START_Y = 0

    # ==================== BACKDROP COLORS ====================
    # Colors for different asset types (hex format for Nuke)
    BACKDROP_COLORS = {
        "plates": 0x4a5a3aFF,      # Olive green
        "3d_renders": 0x3a4a5aFF,  # Steel blue
        "2d_renders": 0x3a5a5aFF,  # Teal
        "rotos": 0x5a3a4aFF,       # Purple
        "cameras": 0x5a4a3aFF,     # Brown
        "default": 0x3f3f3fFF      # Dark gray
    }

    # ==================== FILE EXTENSIONS ====================
    IMAGE_EXTENSIONS = [".exr", ".dpx", ".tif", ".tiff", ".jpg", ".jpeg", ".png"]
    USD_EXTENSIONS = [".usd", ".usda", ".usdc", ".usdz"]

    # ==================== PYSIDE COMPATIBILITY ====================
    @staticmethod
    def get_pyside_module():
        """
        Returns the appropriate PySide module based on Nuke version.
        Nuke 15: PySide2
        Nuke 16+: PySide6
        """
        try:
            import nuke
            nuke_version = nuke.NUKE_VERSION_MAJOR

            if nuke_version >= 16:
                try:
                    from PySide6 import QtWidgets, QtCore, QtGui
                    return QtWidgets, QtCore, QtGui, "PySide6"
                except ImportError:
                    pass

            # Fallback to PySide2
            from PySide2 import QtWidgets, QtCore, QtGui
            return QtWidgets, QtCore, QtGui, "PySide2"

        except Exception as e:
            # If not in Nuke environment, try both
            try:
                from PySide6 import QtWidgets, QtCore, QtGui
                return QtWidgets, QtCore, QtGui, "PySide6"
            except ImportError:
                from PySide2 import QtWidgets, QtCore, QtGui
                return QtWidgets, QtCore, QtGui, "PySide2"

    # ==================== STAMPS INTEGRATION ====================
    STAMPS_PATHS = [
        os.path.expanduser("~/.nuke"),
        os.path.expanduser("~/.nuke/stamps"),
    ]

    ENABLE_STAMPS = True  # Set to False to disable Stamps integration

    # ==================== CACHE ====================
    ENABLE_CACHE = True
