"""Loader-owned nodes in the scene: ownership tag, duplicate clones,
matching Reads/Cameras back to asset rows, node-graph status markers."""

import os
import re
from typing import Iterator, List, Optional, Tuple

import nuke

from ..core.config import Config
from ..core.asset_item import AssetItem
from ..core.versions import extract_version_from_path, version_int
from .utils import knob_value, set_knob

LOADER_TAG = "fromShotLoader"
DUP_INDEX = "dup_index"
DUP_OF = "dup_of"
DUP_OF_TYPE = "dup_of_type"

# Custom knobs the loader adds; pre-seeded on clones before readKnobs,
# otherwise Nuke rejects the whole buffer ("no such knob").
_CUSTOM_KNOBS = (
    (LOADER_TAG, "Boolean_Knob"),
    (DUP_INDEX, "Int_Knob"),
    (DUP_OF, "String_Knob"),
    (DUP_OF_TYPE, "String_Knob"),
)

# Suffix Nuke appends to a pasted copy ("Read3" -> "Read31" / "Read3_1").
_COPY_SUFFIX_RE = re.compile(r'_?\d+$')

# .../Shots/<SQ>/<SH>/Renders/<bucket>/<asset>/v###/...
_ASSET_PATH_RE = re.compile(
    r'/[Ss]hots/([^/]+)/([^/]+)/Renders/(external|3dRender|2dRender)/([^/]+)/v\d{3,4}',
    re.IGNORECASE,
)

STATUS_MARKER = "»"
# Node-graph mirror of the table status: (label text, tile_color 0xRRGGBBAA).
NODE_STATUS_VISUALS = {
    "up_to_date": ("up to date", 0x3a5a3aff),
    "up_to_date_missing": ("up to date (frames missing)", 0x1e3a1eff),
    "to_update": ("to update", 0x4477ccff),
    "to_update_missing": ("to update (frames missing)", 0xcc8844ff),
    "frozen": ("frozen", 0x3f6a80ff),
}


# ---------------------------------------------------------------------------
# Ownership / duplicate tags
# ---------------------------------------------------------------------------

def tag_as_loader_owned(node):
    """Add a read-only `fromShotLoader` checkbox so the loader can tell its
    own Reads from manually imported ones sharing the same path."""
    try:
        knob = node.knob(LOADER_TAG)
        if knob is None:
            knob = nuke.Boolean_Knob(LOADER_TAG, LOADER_TAG)
            node.addKnob(knob)
        knob.setValue(True)
        knob.setEnabled(False)
    except Exception as e:
        print(f"[NukeNodeBuilder] Could not tag node {node.name()} as loader-owned: {e}")


def is_loader_owned(node) -> bool:
    try:
        knob = node.knob(LOADER_TAG)
        return knob is not None and bool(knob.value())
    except Exception:
        return False


def dup_index(node) -> int:
    """0 for a canonical node, N for the N-th "Duplicate Selected" clone."""
    try:
        knob = node.knob(DUP_INDEX)
        return int(knob.value() or 0) if knob is not None else 0
    except Exception:
        return 0


def _dup_parent(node) -> Tuple[str, str]:
    """(parent asset_type, parent asset_name) stamped on a clone."""
    of_knob, type_knob = node.knob(DUP_OF), node.knob(DUP_OF_TYPE)
    if of_knob is None or type_knob is None:
        return "", ""
    try:
        return (type_knob.value() or "").strip(), (of_knob.value() or "").strip()
    except Exception:
        return "", ""


def write_dup_metadata(node, index: int, parent_type: str, parent_name: str):
    for name, ctor, value in (
        (DUP_INDEX, nuke.Int_Knob, index),
        (DUP_OF, nuke.String_Knob, parent_name),
        (DUP_OF_TYPE, nuke.String_Knob, parent_type),
    ):
        try:
            if node.knob(name) is None:
                node.addKnob(ctor(name, name))
            node[name].setValue(value)
        except Exception as e:
            print(f"[ShotAssetLoader] Failed to write {name} on {node.name()}: {e}")


def iter_reads_and_cameras() -> Iterator:
    yield from nuke.allNodes("Read")
    yield from nuke.allNodes("Camera3")


def iter_duplicates(loader_owned_only: bool = True) -> Iterator[Tuple[object, int, str, str]]:
    """(node, dup_index, parent_type, parent_name) for every clone node.
    Bails on the (usually absent) dup_index knob first to stay cheap."""
    for node in iter_reads_and_cameras():
        index = dup_index(node)
        if index <= 0:
            continue
        if loader_owned_only and not is_loader_owned(node):
            continue
        parent_type, parent_name = _dup_parent(node)
        if parent_type and parent_name:
            yield node, index, parent_type, parent_name


def next_dup_index(asset_type: str, asset_name: str) -> int:
    """Highest dup_index of the family + 1, so numbering keeps moving
    forward even after intermediate clones were deleted."""
    indices = [i for _, i, t, n in iter_duplicates(loader_owned_only=False)
               if t == asset_type and n == asset_name]
    return max(indices, default=0) + 1


# ---------------------------------------------------------------------------
# Cloning
# ---------------------------------------------------------------------------

def clone_node(source):
    """New node of the same class with every non-default knob copied via
    writeKnobs/readKnobs (what Save Selection round-trips), so gizmo
    internals, animation and expressions come along."""
    try:
        buffer = source.writeKnobs(nuke.WRITE_NON_DEFAULT_ONLY | nuke.TO_SCRIPT)
        clone = nuke.createNode(source.Class(), inpanel=False)
        for name, ctor_name in _CUSTOM_KNOBS:
            if source.knob(name) is not None and clone.knob(name) is None:
                try:
                    clone.addKnob(getattr(nuke, ctor_name)(name, name))
                except Exception as e:
                    print(f"[ShotAssetLoader] Failed to pre-seed knob {name} on clone of {source.name()}: {e}")
        clone.readKnobs(buffer)
        return clone
    except Exception as e:
        print(f"[ShotAssetLoader] Failed to clone {source.name()}: {e}")
        return None


def find_downstream_cleanup(read_node):
    """The ILGC_ReadCleanup fed by `read_node`, if any."""
    try:
        for node in nuke.allNodes(Config.READ_CLEANUP_GIZMO):
            try:
                if node.input(0) is read_node:
                    return node
            except Exception:
                continue
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Matching scene nodes to asset rows
# ---------------------------------------------------------------------------

def parse_asset_path(file_path: str) -> Optional[dict]:
    """Shot context + asset info of a Prism render path, None otherwise."""
    if not file_path:
        return None
    m = _ASSET_PATH_RE.search(file_path.replace('\\', '/'))
    if not m:
        return None
    sequence, shot, bucket, asset_name = m.groups()
    bucket = bucket.lower()
    if bucket == "external":
        asset_type = "Roto" if asset_name.lower() == Config.ROTO_FOLDER else "Plate"
        source_type = "external"
    elif bucket == "3drender":
        asset_type, source_type = "3D Render", "3dRender"
    else:
        asset_type, source_type = "2D Render", "2dRender"
    return {"sequence": sequence, "shot": shot, "asset_type": asset_type,
            "asset_name": asset_name, "source_type": source_type}


def file_path(node) -> str:
    knob = node.knob("file")
    if knob is None:
        return ""
    return (knob.value() or "").replace('\\', '/')


def loader_reads_for_shot(read_nodes, sequence: str, shot: str) -> List[Tuple[object, str, str]]:
    """(read, path, lowercase path) for canonical loader Reads of the shot.
    Clones are excluded: they are bound to their own row at populate time."""
    result = []
    for read in read_nodes:
        if not is_loader_owned(read) or dup_index(read) > 0:
            continue
        path = file_path(read)
        if path and sequence in path and shot in path:
            result.append((read, path, path.lower()))
    return result


_VERSION_TOKEN_RE = re.compile(r"v\d{3,4}", re.IGNORECASE)


def version_free(path: str) -> str:
    """Identity of a file across versions: the path with version tokens folded."""
    return _VERSION_TOKEN_RE.sub("v#", path.replace("\\", "/").lower())


def find_nodes_for_asset(item: AssetItem, loader_reads, camera_nodes, sequence: str, shot: str):
    """(nodes, has_duplicates): the scene nodes loaded for `item`, one per
    layer / file of the asset.

    Cameras: the canonical CAM_SHOT, else a Camera3 whose file matches the
    shot's camera export. Reads: loader Reads whose path contains
    /<asset_name>/ (and the row's version for rotos, one row per version).
    Reads pointing at the same file up to the version are copies of each
    other: the one without a copy suffix wins, else the highest version and
    the row is flagged as duplicated.
    """
    if item.asset_type == "Camera":
        camera = _find_camera(item, camera_nodes, sequence, shot)
        return ([camera] if camera is not None else []), False

    needle = f"/{item.asset_name.lower()}/"
    candidates = [(r, p) for r, p, p_lower in loader_reads if needle in p_lower]
    if item.asset_type == "Roto":
        candidates = [c for c in candidates if extract_version_from_path(c[1]) == item.versions[0]]

    same_file = {}
    for read, path in candidates:
        same_file.setdefault(version_free(path), []).append((read, path))
    nodes, duplicated = [], False
    for key in sorted(same_file):
        copies = same_file[key]
        originals = [c for c in copies if not _COPY_SUFFIX_RE.search(c[0].name())]
        if len(copies) == 1 or len(originals) == 1:
            nodes.append((originals or copies)[0][0])
            continue
        pool = sorted(originals or copies, key=lambda c: version_int(extract_version_from_path(c[1])), reverse=True)
        print(f"[ShotAssetLoader] WARNING: duplicate loader Reads for {item.asset_type} "
              f"'{item.asset_name}': {', '.join(c[0].name() for c in pool)}")
        nodes.append(pool[0][0])
        duplicated = True
    return nodes, duplicated


def _find_camera(item, camera_nodes, sequence, shot):
    for cam in camera_nodes:
        if cam.name().upper() == Config.CAMERA_NODE_NAME:
            return cam
    for cam in camera_nodes:
        path = file_path(cam)
        if sequence in path and shot in path and f"/{item.asset_name}/" in path:
            return cam
    # Hand-edited / slightly different layouts: accept any camera export of
    # this shot (a shot ships one camera).
    if sequence and shot:
        anchor = f"export/{Config.CAMERA_FOLDER}".lower()
        seq_lc, shot_lc = sequence.lower(), shot.lower()
        for cam in camera_nodes:
            path = file_path(cam).lower()
            if seq_lc in path and shot_lc in path and anchor in path:
                return cam
    return None


# ---------------------------------------------------------------------------
# Node-graph status
# ---------------------------------------------------------------------------

def set_status_marker(node, status_key: str):
    """Tile color + a '» <status>' label line; other label lines are kept."""
    text, tile_color = NODE_STATUS_VISUALS[status_key]
    try:
        set_knob(node, "tile_color", tile_color)
    except Exception as e:
        print(f"[ShotAssetLoader] tile_color sync failed for {node.name()}: {e}")
    try:
        if node.knob("label") is None:
            return
        current = knob_value(node, "label") or ""
        lines = [ln for ln in current.split('\n') if not ln.startswith(STATUS_MARKER)]
        lines.append(f"{STATUS_MARKER} {text}")
        set_knob(node, "label", '\n'.join(lines))
    except Exception as e:
        print(f"[ShotAssetLoader] label sync failed for {node.name()}: {e}")


def layer_folder(node, layers):
    """Folder of `node`'s layer among a version's {layer: folder}: the layer
    named like the folder holding the node's file, else the "rgb" layer of
    files stored directly in the version folder; None when the version has
    no such layer."""
    folder_name = os.path.basename(os.path.dirname(file_path(node)))
    if folder_name in layers:
        return layers[folder_name]
    if _VERSION_TOKEN_RE.fullmatch(folder_name) and "rgb" in layers:
        return layers["rgb"]
    return None


def reload_read(node):
    """Flush a Read's frame cache (no-op for other classes)."""
    if node is None or node.Class() != "Read" or node.knob("reload") is None:
        return
    try:
        node["reload"].execute()
    except Exception as e:
        print(f"[ShotAssetLoader] reload knob failed for {node.name()}: {e}")
