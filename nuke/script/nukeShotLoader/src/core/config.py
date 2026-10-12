"""Static configuration: project layout, node-graph layout, colors, extensions."""

import os


class Config:
    # ---- Project layout (relative to the Prism project root) -------------
    DEFAULT_PROJECT_ROOT = r"I:\McDonald_2511"
    SHOTS_PATH = "03_Production/Shots"
    PIPELINE_PATH = "00_Pipeline"
    PIPELINE_JSON = "pipeline.json"
    PROJECT_THUMBNAIL = "00_Pipeline/project.jpg"
    PREFS_DIR = "04_Resources/Nuke/prefs/shotloader"

    # ---- Asset folders (relative to a shot folder) ------------------------
    PLATES_PATH = "Renders/external"
    RENDERS_3D_PATH = "Renders/3dRender"
    RENDERS_2D_PATH = "Renders/2dRender"
    CAMERA_PATH = "Export"
    CAMERA_FOLDER = "_layer_cam_camera"
    ROTO_FOLDER = "roto"
    STMAPS_FOLDER = "stMaps"

    # ---- Versions ---------------------------------------------------------
    VERSION_PATTERN = r"v(\d{3,4})"
    IGNORE_VERSION_SUFFIXES = ["(mp4)", "(mov)", "(preview)", "_thumbs", "Thumbs.db"]

    # ---- File extensions --------------------------------------------------
    IMAGE_EXTENSIONS = [".exr", ".dpx", ".tif", ".tiff", ".jpg", ".jpeg", ".png", ".psd"]
    USD_EXTENSIONS = [".usd", ".usda", ".usdc", ".usdz"]

    # ---- Node graph layout ------------------------------------------------
    START_X = 0
    START_Y = 0
    READS_PER_ROW = 10
    READ_COL_SPACING = 360
    READ_ROW_HEIGHT = 300
    BACKDROP_PADDING = 150
    BACKDROP_Y_GAP = 50
    ANCHOR_OFFSET = 150            # Read/Camera -> anchor stamp
    ANCHOR_OFFSET_CLEANUP = 50     # ILGC_ReadCleanup -> anchor stamp
    WIRED_OFFSET = 50              # anchor -> wired stamp

    BACKDROP_COLORS = {
        "plates": 0x4a5a3aFF,
        "3d_renders": 0x3a4a5aFF,
        "2d_renders": 0x3a5a5aFF,
        "rotos": 0x5a3a4aFF,
        "cameras": 0x5a4a3aFF,
        "default": 0x3f3f3fFF,
    }

    # ---- Pipeline nodes ---------------------------------------------------
    CAMERA_NODE_NAME = "CAM_SHOT"
    READ_CLEANUP_GIZMO = "ILGC_ReadCleanup"

    # ---- Stamps -----------------------------------------------------------
    ENABLE_STAMPS = True
    STAMPS_PATHS = [
        os.path.expanduser("~/.nuke"),
        os.path.expanduser("~/.nuke/stamps"),
    ]

    # ---- UI ---------------------------------------------------------------
    LOGO_PATH = r"R:/logos/logo.png"
    LOGO_OPACITY = 0.25
    HELP_URL = "https://www.notion.so/illogic/Nuke-Shot-Loader-3679d24ae7e3804491f7ceade8e2a1e3"
    AUTO_REFRESH_MS = 15000

    # ---- Sanity check (before a Render Manager submission) ------------------
    NETWORK_ROOTS = ("I:/", "R:/", "B:/")      # what the farm can read
    LOCAL_COPY_PATH = "Renders/fromLocal"      # in the shot folder: copies of off-network files
    BBOX_TOLERANCE = 0.20                      # bounding box allowed beyond the script format

    # ---- Deadline ---------------------------------------------------------
    # Submitter defaults primed before each Render Manager submission.
    # EnforceRenderOrder is what makes the farm render precomps before the
    # Writes reading them. SubmitScene is left to the studio submitter
    # (CustomSanityChecks.py sets it on).
    DEADLINE_STICKY = {
        "Priority": "90",
        "FrameListMode": "Global",
        "EnforceRenderOrder": "True",
        "BatchMode": "True",
    }
