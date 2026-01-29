from pathlib import Path
from datetime import datetime
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


LAYER_DEP_CONFIG = Path(__file__).resolve().parents[1] / "config.json"

# lightweight cache to avoid repeated scans for the same directory/key
_LATEST_CACHE = {}
_LATEST_CACHE_LOCK = threading.Lock()


def load_layers_list():
    """Return list of layer names from config.json. Expected shape: {"layers": ["_layer_a", ...]}"""
    default = ["_layer_anm_master", "_layer_cfx_master"]
    if LAYER_DEP_CONFIG.exists():
        with LAYER_DEP_CONFIG.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict) and "layers" in data and isinstance(data["layers"], list):
                return [str(x) for x in data["layers"]]
    return default


def _cache_get(key):
    with _LATEST_CACHE_LOCK:
        return _LATEST_CACHE.get(key)


def _cache_set(key, value):
    with _LATEST_CACHE_LOCK:
        _LATEST_CACHE[key] = value


def get_latest_file(directory: Path, patterns=("*.usdc", "*.usda"), ignore_contains=None):
    """Return (mtime, path) of latest file in directory matching patterns. Optionally ignore files whose name contains ignore_contains substring.
    Returns None if directory doesn't exist or no matching files.
    Uses an in-memory cache keyed by directory+patterns+ignore_contains.
    """
    key = (str(directory), tuple(patterns), ignore_contains)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    if not directory.exists():
        _cache_set(key, None)
        return None

    latest = None
    for pattern in patterns:
        for child in directory.rglob(pattern):
            if not child.is_file():
                continue
            name = child.name.lower()
            if ignore_contains and ignore_contains.lower() in name:
                continue
            try:
                mtime = child.stat().st_mtime
            except OSError:
                continue
            if latest is None or mtime > latest[0]:
                latest = (mtime, str(child))

    _cache_set(key, latest)
    return latest


def fmt_time(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def get_status_tree(root_path: Path):
    """Build status tree for a given root Path.

    New behaviour: For each shot folder, scan Renders/3dRender/* for render names.
    For each render, find the latest usdc under:
      Renders/3dRender/RENDER_NAME/v*/beauty/_usd/  (ignore files with 'mp4' in their name)

    For each layer listed in config.json (Export/LAYER_NAME/v*), find the latest usdc (ignore mp4).
    Compare layer mtime against render mtime: if layer missing -> missing, if layer mtime > render mtime -> outdated, else up-to-date.

    Returns: dict: { seq_name: { shot_name: { render_name: {status, path, prereq_statuses}, ...}, ...}, ... }
    """
    layers = load_layers_list()
    tree = {}

    def process_shot(shot_path: Path):
        renders_root = shot_path / "Renders" / "3dRender"
        export_root = shot_path / "Export"

        renders = {}

        if not renders_root.exists():
            return shot_path.name, renders

        # iterate per-render directory
        for render_dir in [p for p in renders_root.iterdir() if p.is_dir()]:
            render_name = render_dir.name

            # latest render usdc under v*/beauty/_usd
            latest_render = get_latest_file(render_dir / "v*" if True else render_dir, patterns=("*.usdc",), ignore_contains="mp4")

            # fallback: try deeper pattern search directly from render_dir
            if latest_render is None:
                # search for v*/beauty/_usd pattern
                candidates = list(render_dir.rglob("v*"))
                candidate_latest = None
                for v in candidates:
                    if not v.is_dir():
                        continue
                    usd_dir = v / "beauty" / "_usd"
                    if not usd_dir.exists():
                        continue
                    cur = get_latest_file(usd_dir, patterns=("*.usdc",), ignore_contains="mp4")
                    if cur is None:
                        continue
                    if candidate_latest is None or cur[0] > candidate_latest[0]:
                        candidate_latest = cur
                latest_render = candidate_latest

            # If still None, mark render as missing (no usd)
            prereq_statuses = []
            for layer in layers:
                layer_dir = export_root / layer
                layer_latest = None
                vdirs = []
                if layer_dir.exists():
                    vdirs = [p for p in layer_dir.iterdir() if p.is_dir() and p.name.startswith("v")]
                    for vdir in vdirs:
                        cur = get_latest_file(vdir, patterns=("*.usdc","*.usda"), ignore_contains="mp4")
                        if cur is None:
                            continue
                        if layer_latest is None or cur[0] > layer_latest[0]:
                            layer_latest = cur

                if layer_latest is None:
                    prereq_statuses.append({"name": layer, "status": "missing", "path": str(layer_dir), "mtime": None, "mtime_str": None})
                else:
                    if latest_render is None:
                        prereq_statuses.append({"name": layer, "status": "up-to-date", "path": layer_latest[1], "mtime": layer_latest[0], "mtime_str": fmt_time(layer_latest[0])})
                    else:
                        layer_mtime = layer_latest[0]
                        render_mtime = latest_render[0]
                        st = "up-to-date"
                        # Cas spécial pour _layer_lgt_master
                        if layer == "_layer_lgt_master" and layer_mtime > render_mtime:
                            # Chercher la version n-1
                            def extract_version_num(vdir):
                                try:
                                    return int(vdir.name.lstrip("v"))
                                except Exception:
                                    return None
                            vnums = sorted([(extract_version_num(v), v) for v in vdirs if extract_version_num(v) is not None], reverse=True)
                            if len(vnums) >= 2:
                                n1_vnum, n1_vdir = vnums[1]  # version n-1
                                n1_latest = get_latest_file(n1_vdir, patterns=("*.usdc","*.usda"), ignore_contains="mp4")
                                if n1_latest:
                                    n1_mtime = n1_latest[0]
                                    # Si la date de n-1 est très proche du render (moins de 5 min)
                                    if abs(n1_mtime - render_mtime) <= 5*60:
                                        st = "up-to-date"
                                    else:
                                        st = "outdated"
                                else:
                                    st = "outdated"
                            else:
                                st = "outdated"
                        else:
                            if layer_mtime > render_mtime:
                                st = "outdated"
                            else:
                                st = "up-to-date"
                        prereq_statuses.append({"name": layer, "status": st, "path": layer_latest[1], "mtime": layer_latest[0], "mtime_str": fmt_time(layer_latest[0])})

            if latest_render is None:
                render_info = {"status": "missing", "path": str(render_dir), "prereq_statuses": prereq_statuses}
            else:
                # determine overall status: missing if all prereqs missing? otherwise outdated if any outdated else up-to-date
                if any(p.get("status") == "outdated" for p in prereq_statuses):
                    overall = "outdated"
                elif all(p.get("status") == "missing" for p in prereq_statuses):
                    overall = "missing"
                else:
                    overall = "up-to-date"

                render_info = {"status": overall, "path": latest_render[1], "prereq_statuses": prereq_statuses}

            renders[render_name] = render_info

        return shot_path.name, renders

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
            shot_name, renders = fut.result()
            tree.setdefault(seq_name, {})[shot_name] = renders

    return tree
