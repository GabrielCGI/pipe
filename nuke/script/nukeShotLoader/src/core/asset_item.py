"""Asset row model and the asset-type vocabulary shared by UI, prefs and builder."""

from typing import Dict, List, Optional

# asset_type (UI label, prefs key) -> filter source, as shown by the filter pills.
SOURCE_TYPES = {
    "Plate": "external",
    "Roto": "external",
    "3D Render": "3dRender",
    "2D Render": "2dRender",
    "Camera": "Camera",
}

# asset_type -> key of the dict returned by AssetDiscoverer.discover_all_assets.
DISCOVERY_KEYS = {
    "Plate": "plates",
    "3D Render": "3d_renders",
    "2D Render": "2d_renders",
    "Roto": "rotos",
    "Camera": "cameras",
}


def colorspace_key(asset_type: str, asset_name: str, version: Optional[str]) -> str:
    """Key under which NukeNodeBuilder looks up a colorspace override.
    Rotos are keyed per version since every version is loaded."""
    if asset_type == "Roto":
        return f"Roto_{version}"
    return f"{asset_type}_{asset_name}"


def first_layer_path(version_data) -> Optional[str]:
    """Folder of a version entry: the first layer for image assets
    ({layer: folder}), the folder itself for cameras."""
    if isinstance(version_data, dict):
        return next(iter(version_data.values()), None)
    return version_data or None


class AssetItem:
    """One row of the Loader table."""

    def __init__(self, asset_type: str, asset_name: str, versions: List[str],
                 versions_dict: Dict, source_type: str = ""):
        self.asset_type = asset_type
        self.asset_name = asset_name
        self.source_type = source_type
        self.versions = versions
        self.versions_dict = versions_dict
        self.selected_version = versions[-1] if versions else None
        self.selected_colorspace = "Auto"

        # Scene state, filled by the update check. One node per layer / file
        # of the asset (a 3D render with beauty + depth has two Reads).
        self.loaded_nodes = []
        self.loaded_version = None
        self.has_update = False
        self.update_target_version = None
        self.has_duplicates = False          # several loader Reads match this asset
        self.status_text = "Not loaded"
        self.status_color = None

        # Read pointing at another shot's asset (discovered from the scene).
        self.is_foreign = False
        self.foreign_sequence = ""
        self.foreign_shot = ""

        self.is_hidden = False               # listed only when "Show Hidden Assets" is on
        self.is_frozen = False               # pinned to its loaded version, skipped by updates
        self.dup_index = 0                   # 0 = canonical row, 1+ = "Duplicate Selected" clone

    @property
    def loaded_node(self):
        """Primary node (status, freeze, duplicate); None when not loaded."""
        return self.loaded_nodes[0] if self.loaded_nodes else None

    @loaded_node.setter
    def loaded_node(self, node):
        self.loaded_nodes = [node] if node is not None else []

    @property
    def is_scene_bound(self) -> bool:
        """Foreign items and duplicates are bound to a node at populate time
        instead of being matched by path on every check."""
        return self.is_foreign or self.dup_index > 0

    def folder(self, version: Optional[str]) -> Optional[str]:
        if not version:
            return None
        return first_layer_path(self.versions_dict.get(version))

    def display_name(self) -> str:
        name = self.asset_name
        if self.is_foreign:
            name = f"{name}  (from {self.foreign_sequence}/{self.foreign_shot})"
        if self.dup_index:
            name = f"{name}  · copy_{self.dup_index:02d}"
        return name

    def label(self) -> str:
        """'Type/name (copy_NN)' for log lines."""
        suffix = f" (copy_{self.dup_index:02d})" if self.dup_index else ""
        return f"{self.asset_type}/{self.asset_name}{suffix}"
