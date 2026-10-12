"""Per-project prefs JSON: hidden assets, frozen assets, package snapshots.

Path: <project>/04_Resources/Nuke/prefs/shotloader/<project>_prefs_shotloader.json
Every entry is scoped by shot key "<sequence>/<shot>". One file serves every
artist of the project: writes are atomic, and a file that can't be read at
the moment is never written back (it would wipe every shot's prefs).
Persistence never raises — it must not break the dialog.
"""

import os
import re
from typing import List, Optional, Set, Tuple

from .config import Config
from .jsonio import UnreadableJson, atomic_write_json, read_json

_PACKAGE_NAME_RE = re.compile(r'^PKG_v(\d+)$')


class ShotLoaderPrefs:

    def __init__(self, path: Optional[str]):
        self.path = path

    @classmethod
    def for_project(cls, project_root: Optional[str]) -> "ShotLoaderPrefs":
        """Prefs of a detected project, creating an empty file on first use.
        Without a project (or an unwritable disk) the prefs are disabled."""
        if not project_root:
            return cls(None)
        name = os.path.basename(project_root.rstrip(os.sep))
        folder = os.path.join(project_root, *Config.PREFS_DIR.split("/"))
        path = os.path.join(folder, f"{name}_prefs_shotloader.json")
        if os.path.exists(path):
            print(f"[ShotAssetLoader] Prefs file found: {path}")
            return cls(path)
        try:
            os.makedirs(folder, exist_ok=True)
            # Exclusive creation: an existence check failing on a network
            # hiccup must not truncate the project's prefs.
            with open(path, "x", encoding="utf-8") as f:
                f.write("{}\n")
            print(f"[ShotAssetLoader] Created empty prefs file: {path}")
        except FileExistsError:
            pass
        except Exception as e:
            print(f"[ShotAssetLoader] Failed to create prefs file at {path}: {e}")
            return cls(None)
        return cls(path)

    @property
    def available(self) -> bool:
        return bool(self.path)

    # ---- raw I/O ----------------------------------------------------------

    def load(self) -> dict:
        """Current content, {} when missing or unreadable."""
        data = self._read()
        return data if data is not None else {}

    def _read(self) -> Optional[dict]:
        """Content, {} for a missing file, None when it can't be read now."""
        if not self.path:
            return {}
        try:
            data = read_json(self.path)
        except UnreadableJson as e:
            print(f"[ShotAssetLoader] Failed to read prefs: {e}")
            return None
        if data is None:
            return {}
        if not isinstance(data, dict):
            print("[ShotAssetLoader] Prefs root is not a dict, ignoring")
            return None
        return data

    def _modify(self, change) -> bool:
        """Read the file, apply change(data) — which returns False when there
        is nothing to save — and write it back atomically."""
        if not self.path:
            return False
        data = self._read()
        if data is None:
            print(f"[ShotAssetLoader] Prefs not saved: {self.path} can't be read right now")
            return False
        if change(data) is False:
            return False
        try:
            atomic_write_json(self.path, data)
            return True
        except Exception as e:
            print(f"[ShotAssetLoader] Failed to write prefs: {e}")
            return False

    def _remove_entries(self, section: str, shot_key: str, match) -> bool:
        """Drop entries matching `match` and prune empty containers."""
        def change(data):
            shot_map = data.get(section, {})
            entries = shot_map.get(shot_key, [])
            remaining = [e for e in entries if not (isinstance(e, dict) and match(e))]
            if len(remaining) == len(entries):
                return False
            if remaining:
                shot_map[shot_key] = remaining
            else:
                shot_map.pop(shot_key, None)
            if not shot_map:
                data.pop(section, None)
            return True
        return self._modify(change)

    def _add_entry(self, section: str, shot_key: str, entry: dict):
        def change(data):
            entries = data.setdefault(section, {}).setdefault(shot_key, [])
            if entry in entries:
                return False
            entries.append(entry)
            return True
        self._modify(change)

    # ---- hidden assets ----------------------------------------------------

    def hidden(self, shot_key: str) -> Set[Tuple[str, str]]:
        entries = self.load().get("hidden_assets", {}).get(shot_key, [])
        return {(e["type"], e["name"]) for e in entries
                if isinstance(e, dict) and "type" in e and "name" in e}

    def hide(self, shot_key: str, asset_type: str, asset_name: str):
        self._add_entry("hidden_assets", shot_key, {"type": asset_type, "name": asset_name})

    def unhide(self, shot_key: str, asset_type: str, asset_name: str) -> bool:
        return self._remove_entries(
            "hidden_assets", shot_key,
            lambda e: e.get("type") == asset_type and e.get("name") == asset_name,
        )

    # ---- frozen assets ----------------------------------------------------

    def frozen(self, shot_key: str) -> Set[Tuple[str, str, int]]:
        entries = self.load().get("frozen_assets", {}).get(shot_key, [])
        return {(e["type"], e["name"], int(e.get("dup_index", 0) or 0)) for e in entries
                if isinstance(e, dict) and "type" in e and "name" in e}

    def set_frozen(self, shot_key: str, asset_type: str, asset_name: str, dup_index: int, frozen: bool):
        if frozen:
            self._add_entry("frozen_assets", shot_key,
                            {"type": asset_type, "name": asset_name, "dup_index": dup_index})
        else:
            self._remove_entries(
                "frozen_assets", shot_key,
                lambda e: (e.get("type") == asset_type and e.get("name") == asset_name
                           and int(e.get("dup_index", 0) or 0) == dup_index),
            )

    # ---- package snapshots ------------------------------------------------
    # A package records the selected version of every row at Load/Update
    # time so the comp can be rewound to any previous state.

    def packages(self, shot_key: str) -> List[dict]:
        packages = self.load().get("packages", {}).get(shot_key, [])
        return packages if isinstance(packages, list) else []

    def current_package(self, shot_key: str) -> Optional[str]:
        current = self.load().get("current_package", {})
        value = current.get(shot_key) if isinstance(current, dict) else None
        return value if isinstance(value, str) else None

    def set_current_package(self, shot_key: str, name: str):
        def change(data):
            data.setdefault("current_package", {})[shot_key] = name
        self._modify(change)

    def add_package(self, shot_key: str, assets: List[dict], compo_version: str, date: str) -> Optional[str]:
        """Append a PKG_v### snapshot (skipped when identical to the last
        one) and pin it as the shot's current package. Returns the new
        package name, or None when deduplicated or not saved."""
        added = []

        def change(data):
            packages = data.setdefault("packages", {}).setdefault(shot_key, [])
            last = packages[-1] if packages else None
            if not (last and last.get("compo_version", "") == compo_version and last.get("assets") == assets):
                added.append(_next_package_name(packages))
                packages.append({"name": added[0], "compo_version": compo_version,
                                 "date": date, "assets": assets})
            data.setdefault("current_package", {})[shot_key] = packages[-1]["name"]

        return added[0] if self._modify(change) and added else None


def _next_package_name(packages: List[dict]) -> str:
    """Next PKG_v### after the highest existing one (robust to hand edits)."""
    highest = 0
    for pkg in packages:
        m = _PACKAGE_NAME_RE.match(pkg.get("name", ""))
        if m:
            highest = max(highest, int(m.group(1)))
    return f"PKG_v{highest + 1:03d}"
