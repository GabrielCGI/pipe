from pathlib import Path
from datetime import datetime
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


LAYER_DEP_CONFIG = Path(__file__).resolve().parents[1] / "config.json"

# lightweight cache to avoid repeated scans for the same directory+keyword
_LATEST_CACHE = {}
_LATEST_CACHE_LOCK = threading.Lock()


def load_layer_deps():
    default = {"_layer_cfx_master": ["_layer_anm_master"]}
    if LAYER_DEP_CONFIG.exists():
        with LAYER_DEP_CONFIG.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            return {str(k): [str(v) for v in vals] for k, vals in data.items()}
    return default


def get_latest_by_mtime(directory: Path, keyword: str):
    key = (str(directory), str(keyword))
    with _LATEST_CACHE_LOCK:
        if key in _LATEST_CACHE:
            return _LATEST_CACHE[key]

    if not directory.exists():
        _LATEST_CACHE[key] = None
        return None

    latest = None
    # iterate specific patterns to avoid scanning unrelated files
    for pattern in ("*.usda", "*.usdc"):
        for child in directory.rglob(pattern):
            if not child.is_file():
                continue
            if keyword and keyword.lower() not in child.name.lower():
                continue
            try:
                mtime = child.stat().st_mtime
            except OSError:
                continue
            if latest is None or mtime > latest[0]:
                latest = (mtime, str(child))

    with _LATEST_CACHE_LOCK:
        _LATEST_CACHE[key] = latest
    return latest


def fmt_time(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def get_status_tree(root_path: Path):
    """Build status tree for a given root Path.

    Returns: dict: { seq_name: { shot_name: { layer_name: {status, prereqs, path}, ... }, ... }, ... }
    """
    deps = load_layer_deps()
    tree = {}

    def process_shot(shot_path: Path):
        export = shot_path / "Export"
        layers = {}

        for dep_layer, prereqs in deps.items():
            dep_dir = export / dep_layer
            dep_latest = get_latest_by_mtime(dep_dir, "")

            prereq_statuses = []
            for p in prereqs:
                p_dir = export / p
                p_latest = get_latest_by_mtime(p_dir, "")
                if p_latest is None:
                    prereq_statuses.append({"name": p, "status": "missing", "path": str(p_dir), "mtime": None})
                else:
                    p_mtime = p_latest[0]
                    p_path = p_latest[1]
                    if dep_latest is None:
                        p_status = "N/A"
                    else:
                        p_status = "outdated" if p_mtime > dep_latest[0] else "up-to-date"
                    prereq_statuses.append({"name": p, "status": p_status, "path": p_path, "mtime": p_mtime})

            info = {"status": "N/A", "prereqs": list(prereqs), "path": str(dep_dir), "prereq_statuses": prereq_statuses}

            any_present = any(ps.get("status") != "missing" for ps in prereq_statuses)
            if not any_present:
                info["status"] = "N/A"
                layers[dep_layer] = info
                continue

            if dep_latest is None:
                info["status"] = "missing"
                info["path"] = str(dep_dir)
                layers[dep_layer] = info
                continue

            if any(ps.get("status") == "outdated" for ps in prereq_statuses):
                info["status"] = "outdated"
            else:
                info["status"] = "up-to-date"

            info["path"] = dep_latest[1] if dep_latest is not None else str(dep_dir)
            # include mtime for the layer itself when available
            info["mtime"] = dep_latest[0] if dep_latest is not None else None
            layers[dep_layer] = info

        return shot_path.name, layers

    # gather all shots grouped by sequence
    seq_shots = {}
    for seq in root_path.iterdir():
        if not seq.is_dir():
            continue
        shots = [shot for shot in seq.iterdir() if shot.is_dir()]
        if shots:
            seq_shots[seq.name] = shots

    # process shots in parallel
    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
        future_to_seq = {}
        for seq_name, shots in seq_shots.items():
            for shot in shots:
                fut = ex.submit(process_shot, shot)
                future_to_seq[fut] = seq_name

        for fut in as_completed(future_to_seq):
            seq_name = future_to_seq[fut]
            shot_name, layers = fut.result()
            tree.setdefault(seq_name, {})[shot_name] = layers

    return tree
