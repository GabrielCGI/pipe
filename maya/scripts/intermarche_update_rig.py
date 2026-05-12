"""
update_references.py
--------------------
Maya script — replaces the source project root on every reference in the
current scene and repoints each one to the latest available version found
in the equivalent target folder.

Usage (Maya Script Editor):
    import importlib, update_references
    importlib.reload(update_references)
    update_references.run()
"""

import os
import re
import maya.cmds as cmds


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SOURCE_ROOT = "I:/intermarche"
TARGET_ROOT = "C:/Users/g.grapperon/Documents/test/prism-playground/prism_playground"

# Regex that matches a versioned folder such as  v001 / v012 / v123
VERSION_DIR_RE = re.compile(r"^v(\d+)$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _norm(path: str) -> str:
    """Normalise slashes for reliable prefix comparison."""
    return path.replace("\\", "/")


def _remap_root(path: str) -> str | None:
    """
    Return *path* with SOURCE_ROOT replaced by TARGET_ROOT.
    Returns None when the path does not start with the source root.
    """
    norm_path = _norm(path)
    norm_src  = _norm(SOURCE_ROOT)
    if norm_path.lower().startswith(norm_src.lower()):
        return TARGET_ROOT + norm_path[len(norm_src):]
    return None


def _version_key(folder_name: str) -> int:
    """Return the integer version number or -1 when not a version folder."""
    m = VERSION_DIR_RE.match(folder_name)
    return int(m.group(1)) if m else -1


def _latest_versioned_file(version_parent_dir: str, stem: str) -> str | None:
    """
    Scan *version_parent_dir* for vXXX sub-folders and return the path to
    the highest-version file whose name starts with *stem*.

    *stem* is the base name without the version suffix, e.g.
    "vegetablesCarrots_toRig"  (everything before  _vXXX.ext).

    Returns the full path to the best match, or None.
    """
    if not os.path.isdir(version_parent_dir):
        return None

    candidates = []
    for entry in os.scandir(version_parent_dir):
        if not entry.is_dir():
            continue
        ver = _version_key(entry.name)
        if ver < 0:
            continue
        # Look for any file in this version folder whose name starts with stem
        try:
            for f in os.scandir(entry.path):
                if f.is_file() and f.name.startswith(stem):
                    candidates.append((ver, _norm(f.path)))
        except PermissionError:
            pass

    if not candidates:
        return None
    candidates.sort(key=lambda t: t[0])   # ascending; last = highest version
    return candidates[-1][1]


def _build_stem(filename: str) -> str:
    """
    Strip the version token from a filename to get a stable stem.

    "vegetablesCarrots_toRig_v005.usdc"  ->  "vegetablesCarrots_toRig"

    Strategy: find the last  _vNNN  segment (with optional extension) and
    drop everything from there onward.
    """
    base = os.path.splitext(filename)[0]          # drop .usdc / .ma …
    parts = base.split("_")
    # Walk from the right until we find a version token
    for i in range(len(parts) - 1, -1, -1):
        if VERSION_DIR_RE.match(parts[i]):
            return "_".join(parts[:i])
    # No version token found — return the full base name as stem
    return base


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _find_new_path(original_path: str) -> tuple[str | None, str]:
    """
    Given an *original_path*, compute the new path in the target project.

    Returns
    -------
    (new_path, reason)
        new_path : resolved latest-version path, or None on failure
        reason   : human-readable status string
    """
    remapped = _remap_root(original_path)
    if remapped is None:
        return None, f"path does not start with source root — skipped"

    norm = _norm(remapped)

    # Split into:  version_parent_dir / version_folder / filename
    #   e.g.  .../toRig  /  v005  /  vegetablesCarrots_toRig_v005.usdc
    parts = norm.replace("\\", "/").split("/")

    # Locate the version folder index from the right
    ver_idx = None
    for i in range(len(parts) - 1, -1, -1):
        if VERSION_DIR_RE.match(parts[i]):
            ver_idx = i
            break

    if ver_idx is None or ver_idx == len(parts) - 1:
        # No version folder found — keep remapped path as-is
        return norm, "no version folder detected — using remapped path directly"

    version_parent_dir = "/".join(parts[:ver_idx])
    filename           = parts[-1]
    stem               = _build_stem(filename)

    latest = _latest_versioned_file(version_parent_dir, stem)
    if latest is None:
        return None, (
            f"target version folder not found or empty: {version_parent_dir}"
        )

    return latest, "OK"


def _all_references() -> list[str]:
    """Return all reference nodes in the scene (exclude _UNKNOWN_REF_NODE_)."""
    refs = cmds.ls(type="reference") or []
    return [r for r in refs if "_UNKNOWN_REF_NODE_" not in r]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run() -> None:
    refs = _all_references()

    if not refs:
        print("[update_references] No references found in the scene.")
        return

    print("\n" + "=" * 70)
    print(f"[update_references] Processing {len(refs)} reference(s)")
    print("=" * 70)

    success = skipped = failed = 0

    for ref_node in refs:
        # Retrieve the current file path for this reference
        try:
            current_path = cmds.referenceQuery(ref_node, filename=True, withoutCopyNumber=True)
        except RuntimeError:
            print(f"\n  [{ref_node}]  ✗  could not query filename — skipped")
            skipped += 1
            continue

        print(f"\n  [{ref_node}]")
        print(f"    original : {current_path}")

        new_path, reason = _find_new_path(current_path)

        if new_path is None:
            print(f"    ✗  {reason}")
            failed += 1
            continue

        if reason != "OK":
            print(f"    ⚠  {reason}")

        print(f"    new path : {new_path}")

        try:
            cmds.file(new_path, loadReference=ref_node)
            print(f"    ✓  reference updated successfully")
            success += 1
        except RuntimeError as exc:
            print(f"    ✗  Maya error while loading reference: {exc}")
            failed += 1

    print("\n" + "=" * 70)
    print(
        f"[update_references] Done — "
        f"{success} updated, {skipped} skipped, {failed} failed"
    )
    print("=" * 70 + "\n")


