"""Status text/color of a Loader row, derived from loaded vs available versions."""

from typing import Optional, Tuple

from .asset_item import AssetItem
from .coverage import FrameCoverage, FrameRange
from .versions import version_int


class StatusColor:
    UP_TO_DATE = "#3a5a3a"
    UP_TO_DATE_PARTIAL = "#1e3a1e"   # latest loaded but frames missing
    UPDATE_FULL = "#4477cc"
    UPDATE_PARTIAL = "#cc8844"       # also "forward" in a manual selection
    ROLLBACK = "#8844cc"
    DUPLICATE = "#aa2c2c"
    FROZEN = "#3f6a80"


def set_status(item: AssetItem, text: str, color: Optional[str]):
    item.status_text = text
    item.status_color = color


def mark_up_to_date(item: AssetItem, version: str):
    """State right after a successful update to `version`."""
    item.loaded_version = version
    item.has_update = False
    item.update_target_version = version
    set_status(item, f"Up to date ({version})", StatusColor.UP_TO_DATE)


def mark_not_loaded(item: AssetItem, text: str = "Not loaded"):
    item.loaded_node = None
    item.loaded_version = None
    item.has_update = False
    set_status(item, text, None)


def apply_update_target(item: AssetItem, coverage: FrameCoverage, scene_range: FrameRange) -> bool:
    """Pick the best update target for a loaded item and set its status.
    Returns True when an update is flagged."""
    target, is_full = coverage.pick_update_target(item, scene_range)
    item.update_target_version = target
    loaded = version_int(item.loaded_version)

    if target and version_int(target) > loaded:
        item.has_update = True
        set_status(item, *_update_status(item, target, is_full, coverage, scene_range))
        return True

    # Up to date against the best full version; a higher partial one is
    # still offered as an update the artist may choose to apply.
    if is_full and item.versions:
        highest = max(item.versions, key=version_int)
        if version_int(highest) > loaded:
            item.has_update = True
            item.update_target_version = highest
            set_status(item, *_update_status(item, highest, False, coverage, scene_range))
            return True

    item.has_update = False
    set_status(item, *_up_to_date_status(item, coverage, scene_range))
    return False


def _update_status(item, target, is_full, coverage, scene_range) -> Tuple[str, str]:
    # A foreign asset has its own frame range: show it instead of a
    # "frames missing" count that only makes sense for the local shot.
    if item.is_foreign:
        rng = coverage.frame_range(item, target)
        detail = f"{rng[0]}-{rng[1]}" if rng else "no frames on disk"
        return f"Update: {item.loaded_version} → {target} ({detail})", StatusColor.UPDATE_FULL
    if is_full:
        return f"Update: {item.loaded_version} → {target} (full)", StatusColor.UPDATE_FULL
    missing = coverage.missing_count(item, target, scene_range)
    miss_text = f"{missing} frames missing" if missing else "frames missing"
    return f"Update: {item.loaded_version} → {target} ({miss_text})", StatusColor.UPDATE_PARTIAL


def _up_to_date_status(item, coverage, scene_range) -> Tuple[str, str]:
    loaded = item.loaded_version
    if item.is_foreign:
        rng = coverage.frame_range(item, loaded)
        text = f"Up to date ({loaded}, {rng[0]}-{rng[1]})" if rng else f"Up to date ({loaded})"
        return text, StatusColor.UP_TO_DATE
    missing = coverage.missing_count(item, loaded, scene_range)
    if missing:
        return f"Up to date ({loaded}, {missing} frames missing)", StatusColor.UP_TO_DATE_PARTIAL
    return f"Up to date ({loaded})", StatusColor.UP_TO_DATE


def apply_manual_selection(item: AssetItem):
    """Status after the artist picks a version in the dropdown: Update,
    Rollback or Up to date relative to the loaded version. The update
    target becomes exactly what the dropdown shows."""
    if not item.loaded_node or not item.loaded_version or item.has_duplicates:
        return
    selected = version_int(item.selected_version)
    loaded = version_int(item.loaded_version)
    item.update_target_version = item.selected_version
    item.has_update = selected != loaded
    if selected < loaded:
        set_status(item, f"Rollback: {item.loaded_version} → {item.selected_version}", StatusColor.ROLLBACK)
    elif selected > loaded:
        set_status(item, f"Update: {item.loaded_version} → {item.selected_version}", StatusColor.UPDATE_PARTIAL)
    else:
        set_status(item, f"Up to date ({item.loaded_version})", StatusColor.UP_TO_DATE)


def apply_duplicate_override(item: AssetItem):
    """Several loader Reads match the asset: block updates until cleaned."""
    item.has_update = False
    item.update_target_version = None
    set_status(item, "Duplicate detected — clean up extras", StatusColor.DUPLICATE)


def apply_freeze_override(item: AssetItem):
    item.has_update = False
    item.update_target_version = None
    set_status(item, f"Freeze ({item.loaded_version or item.selected_version or '?'})", StatusColor.FROZEN)


def node_status_key(item: AssetItem) -> Optional[str]:
    """Key of the node-graph status visual, None when no marker applies."""
    has_missing = "frames missing" in item.status_text
    if item.has_update:
        return "to_update_missing" if has_missing else "to_update"
    if item.loaded_version:
        return "up_to_date_missing" if has_missing else "up_to_date"
    return None
