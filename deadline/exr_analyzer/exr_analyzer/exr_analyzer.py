"""
EXR Sequence Analyzer
Analyse les métadonnées et détecte les pixels excessifs dans une séquence d'images EXR.
"""

import sys
import os
import json
import argparse
import csv
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
import concurrent.futures

# Force UTF-8 sur Windows (terminal cp1252 ne supporte pas ✓ ⚠ ═ etc.)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import numpy as np
except ImportError:
    print("[ERREUR] numpy manquant. Lancez : pip install numpy")
    sys.exit(1)

try:
    import OpenEXR
except ImportError:
    print("[ERREUR] openexr manquant. Lancez : pip install -r requirements.txt")
    sys.exit(1)

# Détection de l'API disponible
# - Ancienne API (OpenEXR ≤ 2.x) : OpenEXR.InputFile + Imath.PixelType
# - Nouvelle API (openexr ≥ 3.x)  : OpenEXR.File, canaux numpy natifs
_NEW_API = hasattr(OpenEXR, "File")

# Imath optionnel — uniquement nécessaire pour l'ancienne API
_Imath = None
if not _NEW_API:
    try:
        import Imath as _Imath
    except ImportError:
        try:
            import imath as _Imath
        except ImportError:
            print("[ERREUR] Imath introuvable. Installez openexr>=3.2.0 : pip install openexr")
            sys.exit(1)


# ──────────────────────────────────────────────
#  Chargement de la config
# ──────────────────────────────────────────────

def _load_config() -> dict:
    cfg_path = Path(__file__).parent / "config.json"
    try:
        with open(cfg_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

_CONFIG = _load_config()

def _lookup_vram_gb(gpu_label: str) -> Optional[float]:
    """Retourne la VRAM réelle (GB) d'un GPU depuis config.json par substring matching.
    La recherche est case-insensitive. L'entrée la plus longue qui matche est préférée
    (ex: 'RTX 4070 Ti SUPER' avant 'RTX 4070 Ti' avant 'RTX 4070').
    Retourne None si aucune entrée ne correspond.
    """
    table = {k: v for k, v in _CONFIG.get("gpu_vram_gb", {}).items()
             if not k.startswith("_")}
    label_low = gpu_label.lower()
    best_key, best_val = None, None
    for key, val in table.items():
        if key.lower() in label_low:
            if best_key is None or len(key) > len(best_key):
                best_key, best_val = key, val
    return float(best_val) if best_val is not None else None


# ──────────────────────────────────────────────
#  Structures de données
# ──────────────────────────────────────────────

@dataclass
class FrameResult:
    filepath: str
    frame_number: Optional[int]

    # Métadonnées machine
    hostname: Optional[str] = None
    gpu_name: Optional[str] = None
    cpu_name: Optional[str] = None
    xpu_mode: Optional[str] = None        # "GPU", "CPU", "HYBRID", "UNKNOWN"
    xpu_gpu_ratio: Optional[float] = None # 0.0 → 1.0 (part GPU)
    render_devices: list = field(default_factory=list)  # [{name, type, contrib_pct, samples, ...}]
    render_time_s: Optional[float] = None  # Wallclock render time (secondes)
    peak_memory_gb: Optional[float] = None # Peak mémoire système (Go)
    vram_peak_gb: Optional[float] = None   # Peak VRAM GPU (Go) — somme des devices GPU

    # Canaux disponibles
    channels: list = field(default_factory=list)

    # Analyse pixels excessifs
    has_excessive_pixels: bool = False
    excessive_pixel_count: int = 0
    excessive_max_r: Optional[float] = None
    excessive_max_g: Optional[float] = None
    excessive_max_b: Optional[float] = None
    excessive_threshold: float = 5.0

    # Erreur éventuelle
    error: Optional[str] = None

    # Avertissement non-bloquant (ex : chunk table hors-spec, lisible par Nuke/mplay)
    warning: Optional[str] = None

    # Données détaillées pour le panneau expandable (extraites de husk:render_stats)
    render_stats_detail: Optional[dict] = None


# ──────────────────────────────────────────────
#  Lecture EXR
# ──────────────────────────────────────────────

_CHUNK_ERRORS = ("chunk", "part number", "bad_chunk", "scanline information")

def _open_exr(path: str):
    """
    Ouvre un fichier EXR et retourne (file_obj, header_dict, channels_list, fallback).

    fallback=True signifie que l'API stricte a échoué (chunk table hors-spec) et qu'on
    est passé sur InputFile — la lecture pixels ne sera pas disponible, mais le fichier
    est considéré valide (lisible par Nuke/mplay).
    """
    if _NEW_API:
        # OpenEXR 3.x : OpenEXR.File
        try:
            f = OpenEXR.File(path)
            header = dict(f.header())
            channels = list(f.channels().keys())
            return f, header, channels, False
        except Exception as e:
            # Certains renderers (Karma XPU, Arnold...) produisent des EXR avec une
            # table de chunks légèrement hors-spec. La lib C++ émet des avertissements
            # vers stderr et lève "Unable to query scanline information". Nuke/mplay
            # les lisent sans problème via leur propre implémentation tolérante.
            err = str(e).lower()
            if any(k in err for k in _CHUNK_ERRORS):
                f = OpenEXR.InputFile(path)
                header = f.header()
                channels = list(header.get("channels", {}).keys())
                return f, header, channels, True   # fallback=True
            raise
    # OpenEXR 2.x : OpenEXR.InputFile
    f = OpenEXR.InputFile(path)
    header = f.header()
    channels = list(header.get("channels", {}).keys())
    return f, header, channels, False


def _read_channel(exr_file, channel_name: str, header: dict,
                  ch_cache: Optional[dict] = None) -> Optional[np.ndarray]:
    """Lit un canal EXR et retourne un ndarray float32.
    ch_cache : dict pré-fetché de exr_file.channels() — évite un appel redondant.
    """
    try:
        use_new = _NEW_API and isinstance(exr_file, OpenEXR.File)
        if use_new:
            # Utiliser le cache si fourni, sinon fetcher (coûteux si appelé N fois)
            ch_dict = ch_cache if ch_cache is not None else exr_file.channels()
            ch = ch_dict.get(channel_name)
            if ch is None:
                return None
            return np.array(ch.pixels, dtype=np.float32)
        else:
            dw = header["dataWindow"]
            width  = dw.max.x - dw.min.x + 1
            height = dw.max.y - dw.min.y + 1
            float_type = _Imath.PixelType(_Imath.PixelType.FLOAT)
            raw = exr_file.channel(channel_name, float_type)
            return np.frombuffer(raw, dtype=np.float32).reshape((height, width))
    except Exception:
        return None


def _extract_rgb_arrays(exr_file, channels: list[str], header: dict) -> dict:
    """
    Retourne un dict {'R': arr, 'G': arr, 'B': arr} en gérant deux cas :
    - Canaux séparés R / G / B (cas standard)
    - Canal unique packagé RGBA (Karma XPU, Houdini, etc.) → on dépaquète
    Le dict channels() est fetché une seule fois et partagé entre les appels.
    """
    CANDIDATES_R = ["R", "r", "red",   "beauty.R", "RGBA.R", "Composite.R"]
    CANDIDATES_G = ["G", "g", "green", "beauty.G", "RGBA.G", "Composite.G"]
    CANDIDATES_B = ["B", "b", "blue",  "beauty.B", "RGBA.B", "Composite.B"]

    result = {}

    # Fetch unique du dict channels (évite N appels redondants)
    ch_cache = exr_file.channels() if (_NEW_API and isinstance(exr_file, OpenEXR.File)) else None

    # Chercher d'abord les canaux séparés
    lower = {c.lower(): c for c in channels}

    def find(candidates):
        for c in candidates:
            if c.lower() in lower:
                return lower[c.lower()]
        return None

    r_ch = find(CANDIDATES_R)
    g_ch = find(CANDIDATES_G)
    b_ch = find(CANDIDATES_B)

    if r_ch and g_ch and b_ch:
        for label, ch in [("R", r_ch), ("G", g_ch), ("B", b_ch)]:
            arr = _read_channel(exr_file, ch, header, ch_cache)
            if arr is not None:
                result[label] = arr.reshape(arr.shape[0], -1)[:, 0] if arr.ndim == 3 else arr
        return result

    # Pas de canaux séparés → chercher un canal packagé RGBA / RGBA_beauty / C etc.
    PACKED_CANDIDATES = ["rgba", "beauty", "combined", "rgb", "color", "c"]
    packed_ch = None
    for c_low, c_orig in lower.items():
        if c_low in PACKED_CANDIDATES or c_low.endswith("rgba") or c_low.endswith("rgb"):
            packed_ch = c_orig
            break
    if packed_ch is None and len(channels) == 1:
        packed_ch = channels[0]

    if packed_ch:
        arr = _read_channel(exr_file, packed_ch, header, ch_cache)
        if arr is not None:
            if arr.ndim == 3 and arr.shape[2] >= 3:
                result["R"] = arr[:, :, 0]
                result["G"] = arr[:, :, 1]
                result["B"] = arr[:, :, 2]
            elif arr.ndim == 2:
                result["R"] = arr
            elif arr.ndim == 3 and arr.shape[2] == 1:
                result["R"] = arr[:, :, 0]

    return result


def _find_channel(available: list[str], candidates: list[str]) -> Optional[str]:
    """Retourne le premier nom de canal trouvé parmi les candidats (insensible à la casse)."""
    lower_available = {c.lower(): c for c in available}
    for candidate in candidates:
        if candidate.lower() in lower_available:
            return lower_available[candidate.lower()]
    return None


# ──────────────────────────────────────────────
#  Parsing Karma renderStatsAnnotation
# ──────────────────────────────────────────────

def _parse_render_stats_annotation(annotation: str) -> list[dict]:
    """
    Parse le texte multilignes de Karma XPU renderStatsAnnotation.
    Retourne une liste de dicts, un par device :
      { index, type, name, contrib_pct, samples, device_mem_gb, threads_used }
    """
    devices = []
    current: Optional[dict] = None

    for raw_line in annotation.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        # Nouvelle section Device N
        if line.startswith("Device ") and line.split()[-1].isdigit():
            if current is not None:
                devices.append(current)
            current = {"index": int(line.split()[-1])}
            continue

        if current is None:
            continue

        # Lignes indentées = sous-métriques (Geometry, Textures…) → ignorer
        if raw_line.startswith("  ") and not raw_line.startswith("Device"):
            continue

        if ":" not in line:
            continue

        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        key_l = key.lower().replace(" ", "_")

        if key_l == "type":
            current["type"] = val  # "Optix", "EmbreeCPU", "CUDA", etc.
        elif key_l == "name":
            current["name"] = val
        elif key_l == "contrib":
            try:
                current["contrib_pct"] = float(val.replace("%", "").strip())
            except ValueError:
                pass
        elif key_l == "samples":
            try:
                current["samples"] = int(val)
            except ValueError:
                pass
        elif key_l == "devicememtotal":
            current["device_mem"] = val          # "13.85 GB"
        elif key_l == "peakdevicememtotal":
            current["peak_device_mem"] = val     # "18.47 GB"
        elif key_l == "threads_used":
            try:
                current["threads_used"] = int(val)
            except ValueError:
                pass

    if current is not None:
        devices.append(current)

    return devices


# ──────────────────────────────────────────────
#  Extraction des métadonnées machine
# ──────────────────────────────────────────────

def _parse_xpu_metadata(header: dict) -> dict:
    """
    Extrait les infos machine depuis les métadonnées EXR.
    Les clés varient selon le moteur de rendu (Arnold, V-Ray, Redshift, Octane, etc.)
    → on inspecte toutes les clés et on fait du pattern matching.
    """
    result = {
        "hostname": None,
        "gpu_name": None,
        "cpu_name": None,
        "render_devices": [],
        "xpu_mode": "UNKNOWN",
        "xpu_gpu_ratio": None,
        "render_time_s": None,
        "peak_memory_gb": None,
        "vram_peak_gb": None,
    }

    # Convertir toutes les valeurs en string pour la recherche
    meta_str: dict[str, str] = {}
    for k, v in header.items():
        try:
            meta_str[k.lower()] = str(v)
        except Exception:
            pass

    # ── Hostname ──────────────────────────────
    # Houdini/Karma : HostComputer = "HOSTNAME - CPU name"
    for key in ("hostcomputer", "hostname", "host", "computername", "machine",
                "renderhost", "arnold/host", "v-ray/renderhost"):
        val = meta_str.get(key)
        if val and val.strip():
            # HostComputer peut contenir "PC-01 - AMD Ryzen ..."  → on garde tout
            result["hostname"] = val.strip()
            # Si le CPU n'est pas encore trouvé et le format est "host - cpu"
            if " - " in val and result["cpu_name"] is None:
                parts = val.split(" - ", 1)
                result["hostname"] = parts[0].strip()
                result["cpu_name"] = parts[1].strip()
            break

    # ── GPU name ─────────────────────────────
    for key in ("gpu", "gpuname", "gpu_name", "renderdevice", "cuda_device",
                "arnoldgpu", "opencl_device", "redshift/gpuname",
                "vray/gpu_name", "octane/gpu"):
        val = meta_str.get(key)
        if val and val.strip():
            result["gpu_name"] = val.strip()
            break

    # ── CPU name ─────────────────────────────
    for key in ("cpu", "cpuname", "cpu_name", "processor",
                "arnold/cpu", "vray/cpu"):
        val = meta_str.get(key)
        if val and val.strip():
            result["cpu_name"] = val.strip()
            break

    # ── Houdini Karma : parser husk:render_stats (JSON) ──────────
    render_stats_raw = meta_str.get("husk:render_stats", "")
    if render_stats_raw:
        try:
            rs = json.loads(render_stats_raw)
            delegate = rs.get("__delegate", "")  # ex: "BRAY_HdKarmaXPU"
            if "xpu" in delegate.lower():
                if result["xpu_mode"] == "UNKNOWN":
                    result["xpu_mode"] = "HYBRID"
            elif "gpu" in delegate.lower():
                result["xpu_mode"] = "GPU"
            elif "cpu" in delegate.lower():
                result["xpu_mode"] = "CPU"

            # ── Parser renderStatsAnnotation ──────────────────────
            annotation = rs.get("renderStatsAnnotation", "")
            if annotation:
                devices = _parse_render_stats_annotation(annotation)
                result["render_devices"] = devices

                # Déduire gpu_name, cpu_name et ratio depuis les devices
                gpu_devices  = [d for d in devices if d.get("type", "").lower()
                                not in ("embreecpu", "cpu", "software")]
                cpu_devices  = [d for d in devices if d.get("type", "").lower()
                                in ("embreecpu", "cpu", "software")]

                if gpu_devices and result["gpu_name"] is None:
                    result["gpu_name"] = gpu_devices[0].get("name")

                if cpu_devices and result["cpu_name"] is None:
                    result["cpu_name"] = cpu_devices[0].get("name")

                # Ratio GPU = somme des contrib GPU / total
                total_contrib = sum(d.get("contrib_pct", 0) for d in devices)
                gpu_contrib   = sum(d.get("contrib_pct", 0) for d in gpu_devices)
                if total_contrib > 0:
                    ratio = gpu_contrib / total_contrib
                    result["xpu_gpu_ratio"] = round(ratio, 4)
                    if ratio >= 0.99:
                        result["xpu_mode"] = "GPU"
                    elif ratio <= 0.01:
                        result["xpu_mode"] = "CPU"
                    else:
                        result["xpu_mode"] = "HYBRID"

            # ── VRAM peak : somme des GPU devices ────────────────
            def _gb_str_to_float(s: str) -> Optional[float]:
                """Convertit '18.47 GB' ou '18.47GB' en float, None si échec."""
                try:
                    return float(s.lower().replace("gb", "").replace("gib", "").strip())
                except (ValueError, AttributeError):
                    return None

            gpu_devs = [d for d in result["render_devices"]
                        if d.get("type", "").lower() not in ("embreecpu", "cpu", "software")]
            vram_total = 0.0
            vram_found = False
            for d in gpu_devs:
                v = _gb_str_to_float(d.get("peak_device_mem", ""))
                if v is None:
                    v = _gb_str_to_float(d.get("device_mem", ""))
                if v is not None:
                    vram_total += v
                    vram_found = True
            if vram_found:
                result["vram_peak_gb"] = round(vram_total, 2)

            # ── Render time (wallclock) ───────────────────────────
            sys_time = rs.get("system_time", {})
            wc = sys_time.get("wallclock") if isinstance(sys_time, dict) else None
            if wc is None:
                xpu_t = rs.get("xpu_timings", {})
                wc = xpu_t.get("render_time") if isinstance(xpu_t, dict) else None
            if wc is not None:
                try:
                    result["render_time_s"] = float(wc)
                except (ValueError, TypeError):
                    pass

            # ── Peak memory système ───────────────────────────────
            sys_mem = rs.get("system_memory", {})
            if isinstance(sys_mem, dict):
                peak = sys_mem.get("peak")
                if peak is not None:
                    try:
                        result["peak_memory_gb"] = round(float(peak) / (1024 ** 3), 1)
                    except (ValueError, TypeError):
                        pass

            # ── Données détaillées (expandable panel) ────────────────
            detail: dict = {}

            # Time to first pixel (Karma stocke en millisecondes)
            ttfp_raw = rs.get("ttfp")
            if ttfp_raw is not None:
                try:
                    ttfp_ms = float(ttfp_raw)
                    # Si ttfp_ms > wallclock*1000 c'est probablement déjà en secondes
                    wc_ref = result.get("render_time_s") or 0
                    detail["ttfp_s"] = ttfp_ms / 1000.0 if ttfp_ms > wc_ref else ttfp_ms
                except (ValueError, TypeError):
                    pass

            # Load time (chargement USD)
            lt = rs.get("load_time", {})
            if isinstance(lt, dict):
                try:
                    detail["load_time_s"] = float(lt.get("wallclock", 0))
                except (ValueError, TypeError):
                    pass

            # RAM système
            sm = rs.get("system_memory", {})
            if isinstance(sm, dict):
                try:
                    to_gb = lambda v: round(float(v) / (1024 ** 3), 1)
                    detail["sys_mem_current_gb"] = to_gb(sm.get("current", 0))
                    detail["sys_mem_peak_gb"]    = to_gb(sm.get("peak", 0))
                    detail["sys_mem_total_gb"]   = to_gb(sm.get("total", 0))
                except (ValueError, TypeError):
                    pass

            # Breakdown mémoire GPU par device (depuis xpu_devices JSON)
            devices_detail = []
            for xpu_dev in rs.get("xpu_devices", []):
                mem = xpu_dev.get("xpu_device_memory", {})
                gb = lambda v: round(float(v) / (1024 ** 3), 2) if v else 0.0
                devices_detail.append({
                    "label":         xpu_dev.get("xpu_device_label", "?"),
                    "type":          xpu_dev.get("xpu_device_type",  "?"),
                    "contrib":       xpu_dev.get("xpu_device_contrib", 0),
                    "used_gb":       gb(mem.get("used",          0)),
                    "peak_gb":       gb(mem.get("peak_used",     0)),
                    "geo_gb":        gb(mem.get("geometry",      0)),
                    "tex_gb":        gb(mem.get("texture",       0)),
                    "vol_gb":        gb(mem.get("volume",        0)),
                    "other_gb":      gb(mem.get("other",         0)),
                    "host_gb":       gb(mem.get("host",          0)),
                    "peak_geo_gb":   gb(mem.get("peak_geometry", 0)),
                    "peak_tex_gb":   gb(mem.get("peak_texture",  0)),
                    "peak_vol_gb":   gb(mem.get("peak_volume",   0)),
                    "peak_other_gb": gb(mem.get("peak_other",    0)),
                    "peak_host_gb":  gb(mem.get("peak_host",     0)),
                })
            detail["devices"] = devices_detail

            # Geometry counts
            gc = rs.get("geometry_counts", {})
            if isinstance(gc, dict):
                detail["geo_polygon_total"]  = gc.get("polygon",    {}).get("total",  0)
                detail["geo_polygon_unique"] = gc.get("polygon",    {}).get("unique", 0)
                detail["geo_curve_total"]    = gc.get("curve",      {}).get("total",  0)
                detail["geo_diced_polys"]    = gc.get("diced_polys",{}).get("total",  0)

            # Ray counts
            rc = rs.get("ray_counts", {})
            if isinstance(rc, dict):
                detail["rays_total"]     = rc.get("total",    0)
                detail["rays_primary"]   = rc.get("primary",  0)
                detail["rays_indirect"]  = rc.get("indirect", 0)
                detail["rays_occlusion"] = rc.get("occlusion",0)

            # Textures OIIO
            oiio = rs.get("oiio_stats", {})
            if isinstance(oiio, dict):
                detail["tex_unique"]          = oiio.get("unique_files", 0)
                detail["tex_disk_gb"]         = round(float(oiio.get("file_size",    0)) / (1024**3), 2)
                detail["tex_uncompressed_gb"] = round(float(oiio.get("image_size",   0)) / (1024**3), 2)
            tex_errors = rs.get("texture_error_files", [])
            detail["tex_missing"] = len(tex_errors) if isinstance(tex_errors, list) else 0

            # AOV buffers
            aov_mem = rs.get("aov_raster_memory", {})
            if isinstance(aov_mem, dict):
                detail["aov_peak_gb"] = round(float(aov_mem.get("peak", 0)) / (1024**3), 2)

            # Render settings
            rs_cfg = rs.get("render_settings", {})
            if isinstance(rs_cfg, dict):
                detail["spp"]         = rs_cfg.get("samplesperpixel")
                detail["max_samples"] = rs_cfg.get("pathtracedsamples")
                detail["mode"]        = rs_cfg.get("imagemode")

            result["render_stats_detail"] = detail

        except (json.JSONDecodeError, TypeError):
            pass

    # ── Software (Karma, Arnold, Redshift…) → déduire le mode ────
    software_val = meta_str.get("software", "")
    if software_val and result["xpu_mode"] == "UNKNOWN":
        sw_low = software_val.lower()
        if "xpu" in sw_low:
            result["xpu_mode"] = "HYBRID"  # Karma XPU = CPU+GPU
        elif "gpu" in sw_low or "cuda" in sw_low or "optix" in sw_low:
            result["xpu_mode"] = "GPU"
        elif "cpu" in sw_low:
            result["xpu_mode"] = "CPU"

    # ── XPU / mode de rendu ──────────────────
    # Chercher des indicateurs de mode GPU/CPU dans toutes les clés
    gpu_keywords  = {"gpu", "cuda", "opencl", "optix", "metal", "vulkan", "rtx"}
    cpu_keywords  = {"cpu-only"}

    mode_found = None
    ratio_found = None

    for k, v in meta_str.items():
        v_low = v.lower()

        # Clé dédiée au ratio XPU (ex: Arnold XPU, Redshift)
        if any(x in k for x in ("xpu", "gpupct", "gpu_pct", "gpu_percent",
                                  "gpuratio", "gpu_ratio", "cpugpu_split")):
            try:
                # Valeur peut être "0.75", "75%", "75 / 25"
                clean = v_low.replace("%", "").split("/")[0].strip()
                ratio = float(clean)
                if ratio > 1.0:
                    ratio /= 100.0
                ratio_found = max(0.0, min(1.0, ratio))
                if ratio_found >= 0.99:
                    mode_found = "GPU"
                elif ratio_found <= 0.01:
                    mode_found = "CPU"
                else:
                    mode_found = "HYBRID"
            except (ValueError, IndexError):
                pass

        if mode_found is None:
            if any(kw in k or kw in v_low for kw in gpu_keywords):
                mode_found = "GPU"
            elif any(kw in k or kw in v_low for kw in cpu_keywords):
                mode_found = "CPU"

    # N'écraser que si le mode n'a pas déjà été défini par une source plus fiable
    if mode_found and result["xpu_mode"] == "UNKNOWN":
        result["xpu_mode"] = mode_found
    if ratio_found is not None:
        result["xpu_gpu_ratio"] = ratio_found

    return result


# ──────────────────────────────────────────────
#  Analyse d'une frame
# ──────────────────────────────────────────────

def analyze_frame(filepath: str, threshold: float = 5.0) -> FrameResult:
    path = Path(filepath)

    # Extraire le numéro de frame depuis le nom de fichier (ex: render.0042.exr)
    frame_number = None
    for part in reversed(path.stem.split(".")):
        if part.isdigit():
            frame_number = int(part)
            break
    if frame_number is None:
        digits = "".join(filter(str.isdigit, path.stem))
        if digits:
            frame_number = int(digits[-8:])

    result = FrameResult(
        filepath=str(filepath),
        frame_number=frame_number,
        excessive_threshold=threshold,
    )

    try:
        if not path.exists():
            result.error = "Fichier introuvable"
            return result

        exr, header, channels_list, chunk_fallback = _open_exr(str(path))

        if chunk_fallback:
            result.warning = "Format tiled/multi-part hors-spec (lisible par Nuke/mplay, analyse pixels ignorée)"

        # Canaux disponibles
        result.channels = channels_list

        # Métadonnées machine
        meta = _parse_xpu_metadata(header)
        result.hostname        = meta["hostname"]
        result.gpu_name        = meta["gpu_name"]
        result.cpu_name        = meta["cpu_name"]
        result.xpu_mode        = meta["xpu_mode"]
        result.xpu_gpu_ratio   = meta["xpu_gpu_ratio"]
        result.render_devices  = meta["render_devices"]
        result.render_time_s        = meta["render_time_s"]
        result.peak_memory_gb       = meta["peak_memory_gb"]
        result.vram_peak_gb         = meta["vram_peak_gb"]
        result.render_stats_detail  = meta.get("render_stats_detail")

        # ── Analyse pixels excessifs ──────────
        # Gère canaux séparés R/G/B ET canaux packagés (RGBA, C, beauty…)
        # Ignoré si fallback chunk (lecture pixels non disponible avec InputFile)
        arrays = {} if chunk_fallback else _extract_rgb_arrays(exr, result.channels, header)

        if arrays:
            labels = list(arrays.keys())
            # Stack en (N, H, W) — une seule allocation mémoire
            stacked = np.nan_to_num(
                np.stack([arrays[l] for l in labels]),
                nan=0.0, posinf=0.0, neginf=0.0
            ).astype(np.float32)

            # Masque global : pixel excessif si AU MOINS un canal dépasse le seuil
            combined_mask = stacked.max(axis=0) > threshold
            result.excessive_pixel_count = int(np.count_nonzero(combined_mask))
            result.has_excessive_pixels  = result.excessive_pixel_count > 0

            # Max par canal en une seule passe sur le tableau stacké
            channel_maxes = stacked.max(axis=(1, 2))
            for i, label in enumerate(labels):
                mx = float(channel_maxes[i])
                if label == "R":
                    result.excessive_max_r = mx
                elif label == "G":
                    result.excessive_max_g = mx
                elif label == "B":
                    result.excessive_max_b = mx

        if hasattr(exr, "close"):
            exr.close()

    except Exception as e:
        result.error = str(e)

    return result


# ──────────────────────────────────────────────
#  Collecte des fichiers
# ──────────────────────────────────────────────

def collect_exr_files(path: str) -> list[str]:
    p = Path(path)
    if p.is_file() and p.suffix.lower() == ".exr":
        return [str(p)]
    elif p.is_dir():
        files = sorted(p.glob("**/*.exr"))
        return [str(f) for f in files]
    else:
        # Glob pattern passé directement
        import glob
        files = sorted(glob.glob(path, recursive=True))
        return [f for f in files if f.lower().endswith(".exr")]


# ──────────────────────────────────────────────
#  Rapports
# ──────────────────────────────────────────────

def print_summary(results: list[FrameResult], threshold: float):
    total    = len(results)
    errors   = [r for r in results if r.error]
    warnings = [r for r in results if r.warning]
    hotspot  = [r for r in results if r.has_excessive_pixels]

    print("\n" + "═" * 64)
    print("  RÉSUMÉ DE L'ANALYSE EXR")
    print("═" * 64)
    print(f"  Frames analysées  : {total}")
    print(f"  Erreurs           : {len(errors)}")
    print(f"  Frames > {threshold:.1f}        : {len(hotspot)}")

    # Résumé par machine
    machines: dict[str, list[FrameResult]] = {}
    for r in results:
        key = r.hostname or "inconnu"
        machines.setdefault(key, []).append(r)

    print("\n  ── Par machine ──────────────────────────────────")
    for host, frames in sorted(machines.items()):
        gpu  = next((f.gpu_name  for f in frames if f.gpu_name),  "N/A")
        cpu  = next((f.cpu_name  for f in frames if f.cpu_name),  "N/A")
        mode = next((f.xpu_mode  for f in frames if f.xpu_mode and f.xpu_mode != "UNKNOWN"), "UNKNOWN")
        ratio_vals = [f.xpu_gpu_ratio for f in frames if f.xpu_gpu_ratio is not None]
        ratio_str  = f"{sum(ratio_vals)/len(ratio_vals)*100:.0f}% GPU" if ratio_vals else ""
        hot = sum(1 for f in frames if f.has_excessive_pixels)
        print(f"  [{host}]")
        print(f"    GPU  : {gpu}")
        print(f"    CPU  : {cpu}")
        print(f"    Mode : {mode}  {ratio_str}")
        print(f"    Frames totales : {len(frames)}  |  avec pixels > {threshold:.1f} : {hot}")

        # Devices Karma XPU si disponibles (prendre le premier frame qui en a)
        sample_devices = next((f.render_devices for f in frames if f.render_devices), None)
        if sample_devices:
            for dev in sample_devices:
                dtype = dev.get("type", "?")
                dname = dev.get("name", "?")
                contrib = dev.get("contrib_pct")
                samples = dev.get("samples")
                devmem  = dev.get("device_mem", "")
                threads = dev.get("threads_used")
                parts = [f"  [{dev.get('index','?')}] {dtype:12s} {dname}"]
                if contrib is not None:
                    parts.append(f"contrib={contrib:.0f}%")
                if samples is not None:
                    parts.append(f"samples={samples}")
                if devmem:
                    parts.append(f"VRAM={devmem}")
                if threads is not None:
                    parts.append(f"threads={threads}")
                print(f"    {'  '.join(parts)}")

    # Détail des frames problématiques
    if hotspot:
        print(f"\n  ── Frames avec pixels excessifs (> {threshold:.1f}) ─────────")
        for r in sorted(hotspot, key=lambda x: x.frame_number or 0):
            maxvals = []
            for label, val in [("R", r.excessive_max_r), ("G", r.excessive_max_g), ("B", r.excessive_max_b)]:
                if val is not None:
                    maxvals.append(f"{label}={val:.2f}")
            print(f"  Frame {r.frame_number:>6} | {r.excessive_pixel_count:>8} px | max: {', '.join(maxvals)}")
            print(f"           └─ {Path(r.filepath).name}  [{r.hostname or '?'}]")

    if warnings:
        print(f"\n  ── Avertissements (non bloquants) ───────────────────")
        for r in warnings:
            print(f"  Frame {str(r.frame_number):>6} | {Path(r.filepath).name}")
            print(f"           └─ ⚠ {r.warning}")

    if errors:
        print(f"\n  ── Erreurs ─────────────────────────────────────────")
        for r in errors:
            print(f"  Frame {str(r.frame_number):>6} | {Path(r.filepath).name}")
            print(f"           └─ {r.error}")

    print("═" * 64 + "\n")


def export_csv(results: list[FrameResult], output_path: str):
    if not results:
        return
    fields = list(asdict(results[0]).keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            d = asdict(r)
            d["channels"] = "|".join(d["channels"])
            writer.writerow(d)
    print(f"  CSV exporté → {output_path}")


def export_json(results: list[FrameResult], output_path: str):
    data = [asdict(r) for r in results]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  JSON exporté → {output_path}")


def export_html(results: list[FrameResult], output_path: str, threshold: float):
    from html import escape
    import datetime

    hotspot = [r for r in results if r.has_excessive_pixels]
    errors  = [r for r in results if r.error]
    total   = len(results)
    ok      = total - len(hotspot) - len(errors)
    hot_pct = f"{len(hotspot)/total*100:.1f}" if total else "0"
    err_pct = f"{len(errors)/total*100:.1f}"  if total else "0"
    seq_name = Path(results[0].filepath).parent.name if results else "—"
    gen_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── Ratio GPU/CPU global (moyenne sur toutes les frames avec données) ──
    all_ratios = [r.xpu_gpu_ratio for r in results if r.xpu_gpu_ratio is not None]
    global_gpu_ratio = sum(all_ratios) / len(all_ratios) if all_ratios else None
    global_cpu_ratio = 1.0 - global_gpu_ratio if global_gpu_ratio is not None else None

    if global_gpu_ratio is not None:
        xpu_global_card = (
            '<div class="scard c-xpu">'
            '<div class="slbl" style="margin-bottom:8px">Ratio XPU séquence</div>'
            '<div class="xpu-global-bar">'
            f'<div class="xpu-global-gpu" style="width:{global_gpu_ratio*100:.1f}%"></div>'
            f'<div class="xpu-global-cpu" style="width:{global_cpu_ratio*100:.1f}%"></div>'
            '</div>'
            '<div class="xpu-global-labels">'
            f'<span class="c-gpu">GPU {global_gpu_ratio*100:.0f}%</span>'
            f'<span class="c-cpu">CPU {global_cpu_ratio*100:.0f}%</span>'
            '</div></div>'
        )
    else:
        xpu_global_card = ""

    # ── Cartes par machine ───────────────────────────────────────────
    machines: dict[str, list[FrameResult]] = {}
    for r in results:
        machines.setdefault(r.hostname or "inconnu", []).append(r)

    machine_cards_html = ""
    for host, frames in sorted(machines.items()):
        gpu  = next((f.gpu_name for f in frames if f.gpu_name), "N/A")
        cpu  = next((f.cpu_name for f in frames if f.cpu_name), "N/A")
        mode = next((f.xpu_mode for f in frames if f.xpu_mode and f.xpu_mode != "UNKNOWN"), "UNKNOWN")
        ratio_vals = [f.xpu_gpu_ratio for f in frames if f.xpu_gpu_ratio is not None]
        gpu_ratio  = sum(ratio_vals) / len(ratio_vals) if ratio_vals else None
        cpu_ratio  = 1.0 - gpu_ratio if gpu_ratio is not None else None
        m_total    = len(frames)
        m_hot      = sum(1 for f in frames if f.has_excessive_pixels)
        m_err      = sum(1 for f in frames if f.error)
        m_ok       = m_total - m_hot - m_err
        m_hot_pct  = m_hot / m_total * 100 if m_total else 0
        m_err_pct  = m_err / m_total * 100 if m_total else 0

        # Barre GPU/CPU ratio
        if gpu_ratio is not None:
            gpu_pct_bar = gpu_ratio * 100
            cpu_pct_bar = cpu_ratio * 100
            ratio_bar = f"""
            <div class="ratio-label">
              <span class="badge gpu">GPU {gpu_pct_bar:.0f}%</span>
              <span class="badge cpu">CPU {cpu_pct_bar:.0f}%</span>
            </div>
            <div class="ratio-bar">
              <div class="ratio-fill-gpu" style="width:{gpu_pct_bar:.1f}%"></div>
              <div class="ratio-fill-cpu" style="width:{cpu_pct_bar:.1f}%"></div>
            </div>"""
        else:
            ratio_bar = f'<div class="ratio-label"><span class="badge mode-{(mode or "unknown").lower()}">{escape(mode or "?")}</span></div>'

        # Devices Karma XPU
        sample_devices = next((f.render_devices for f in frames if f.render_devices), [])
        devices_rows = ""
        for dev in sample_devices:
            dtype   = dev.get("type", "?")
            dname   = dev.get("name", "?")
            contrib = dev.get("contrib_pct")
            samples = dev.get("samples")
            devmem  = dev.get("device_mem", "")
            threads = dev.get("threads_used")
            is_gpu  = dtype.lower() not in ("embreecpu", "cpu", "software")
            dev_cls = "dev-gpu" if is_gpu else "dev-cpu"
            contrib_bar = f'<div class="dev-bar"><div class="dev-bar-fill {"gpu" if is_gpu else "cpu"}" style="width:{contrib:.0f}%"></div></div>' if contrib is not None else ""
            devices_rows += f"""
              <tr class="{dev_cls}">
                <td>{"🖥 GPU" if is_gpu else "⚙ CPU"}</td>
                <td>{escape(dname)}</td>
                <td>{f"{contrib:.0f}%" if contrib is not None else "—"}{contrib_bar}</td>
                <td class="mono">{samples if samples is not None else "—"}</td>
                <td class="mono">{devmem or "—"}</td>
                <td class="mono">{threads if threads is not None else "—"}</td>
              </tr>"""

        devices_table = f"""
          <table class="dev-table">
            <thead><tr><th>Type</th><th>Nom</th><th>Contrib</th><th>Samples</th><th>VRAM</th><th>Threads</th></tr></thead>
            <tbody>{devices_rows}</tbody>
          </table>""" if devices_rows else ""

        # Mini sparkline : barre de frames colorées
        spark_cells = ""
        for f in sorted(frames, key=lambda x: x.frame_number or 0):
            cls = "sp-err" if f.error else ("sp-hot" if f.has_excessive_pixels else "sp-ok")
            fn  = f.frame_number if f.frame_number is not None else "?"
            spark_cells += f'<span class="{cls}" title="Frame {fn}"></span>'

        machine_cards_html += f"""
        <div class="mc">
          <div class="mc-header">
            <div class="mc-title">
              <span class="host-icon">🖥</span>
              <span class="host-name">{escape(host)}</span>
              <span class="mc-mode-badge mode-{(mode or 'unknown').lower()}">{escape(mode or '?')}</span>
            </div>
            <div class="mc-stats">
              <span class="stat-ok">{m_ok} OK</span>
              <span class="stat-hot">⚠ {m_hot} hotspot{"s" if m_hot != 1 else ""}</span>
              <span class="stat-err">✗ {m_err} erreur{"s" if m_err != 1 else ""}</span>
              <span class="stat-total">{m_total} frames</span>
            </div>
          </div>

          <div class="mc-body">
            <div class="mc-info">
              <div class="info-row"><span class="info-lbl">GPU</span><span class="info-val gpu-val">{escape(gpu)}</span></div>
              <div class="info-row"><span class="info-lbl">CPU</span><span class="info-val">{escape(cpu)}</span></div>
              <div class="info-row ratio-row">
                <span class="info-lbl">Ratio XPU</span>
                <div class="ratio-wrap">{ratio_bar}</div>
              </div>
            </div>

            {devices_table}
          </div>

          <div class="spark" title="Frames : vert=OK, orange=hotspot, rouge=erreur">
            {spark_cells}
          </div>
        </div>"""

    # ── Tableau des frames ───────────────────────────────────────────
    frame_rows = ""
    for idx, r in enumerate(results):
        if r.error:
            sc, sl = "tr-err", f'<span class="pill pill-err">✗ Erreur</span>'
        elif r.has_excessive_pixels:
            sc, sl = "tr-hot", f'<span class="pill pill-hot">⚠ {r.excessive_pixel_count:,} px</span>'
        else:
            sc, sl = "tr-ok", '<span class="pill pill-ok">✓ OK</span>'

        chan_vals = [(r.excessive_max_r, "R"), (r.excessive_max_g, "G"), (r.excessive_max_b, "B")]
        chan_vals = [(v, l) for v, l in chan_vals if v is not None]
        if chan_vals:
            top_val, top_lbl = max(chan_vals, key=lambda x: x[0])
            max_cls  = "val-hot" if top_val > threshold else ""
            max_cell = f'<span class="mono {max_cls}">{top_lbl}:{top_val:,.1f}</span>'
        else:
            max_cell = "—"

        if r.render_time_s is not None:
            t = int(r.render_time_s)
            h, rem = divmod(t, 3600)
            m, s   = divmod(rem, 60)
            render_cell = f"{h}h{m:02d}m" if h else f"{m}m{s:02d}s"
        else:
            render_cell = "—"

        mem_cell  = f"{r.peak_memory_gb:.1f} GB" if r.peak_memory_gb is not None else "—"
        vram_cell = f"{r.vram_peak_gb:.1f} GB"   if r.vram_peak_gb  is not None else "—"

        if r.xpu_mode in ("GPU", "HYBRID") and r.gpu_name:
            dev_label = f'<span class="dev-tag gpu-tag">{escape(r.gpu_name)}</span>'
        elif r.cpu_name:
            dev_label = f'<span class="dev-tag cpu-tag">{escape(r.cpu_name)}</span>'
        else:
            dev_label = f'<span class="dev-tag unk-tag">{escape(r.xpu_mode or "—")}</span>'

        if r.xpu_gpu_ratio is not None:
            gpu_p = r.xpu_gpu_ratio * 100
            cpu_p = 100 - gpu_p
            ratio_cell = (
                '<div class="ratio-mini">'
                '<div class="ratio-mini-bar">'
                f'<div class="ratio-mini-gpu" style="width:{gpu_p:.0f}%"></div>'
                '</div>'
                f'<span class="ratio-mini-lbl"><span class="c-gpu">{gpu_p:.0f}%G</span>'
                f' <span class="c-cpu">{cpu_p:.0f}%C</span></span>'
                '</div>'
            )
        else:
            ratio_cell = '<span class="ratio-mini-na">—</span>'

        err_msg = f'<span class="err-msg">{escape(r.error or "")}</span>' if r.error else ""
        has_detail = r.render_stats_detail is not None
        detail_icon = f' <span class="expand-icon" id="icon-{idx}">&#9658;</span>' if has_detail else ''
        frame_num_str = str(r.frame_number) if r.frame_number is not None else '?'
        data_status = "hot" if r.has_excessive_pixels else ("err" if r.error else "ok")
        if has_detail:
            tr_open = f'<tr class="{sc}" data-status="{data_status}" onclick="toggleDetail({idx})" style="cursor:pointer">'
        else:
            tr_open = f'<tr class="{sc}" data-status="{data_status}">'

        frame_rows += f"""
        {tr_open}
          <td class="mono td-frame">{frame_num_str}{detail_icon}</td>
          <td class="td-file mono">{escape(Path(r.filepath).name)}{err_msg}</td>
          <td class="td-host">{escape(r.hostname or '—')}</td>
          <td class="td-device">{dev_label}</td>
          <td class="td-ratio">{ratio_cell}</td>
          <td>{sl}</td>
          <td class="mono td-render">{render_cell}</td>
          <td class="mono td-mem">{mem_cell}</td>
          <td class="mono td-vram">{vram_cell}</td>
          <td class="td-max">{max_cell}</td>
        </tr>"""

        # ── Panneau expandable ──────────────────────────────────────────
        if has_detail:
            d = r.render_stats_detail

            # ── Timings ──────────────────────────────────────────────────
            def fmt_s(v):
                if v is None: return "—"
                v = float(v)
                if v < 60: return f"{v:.1f}s"
                m2, s2 = divmod(int(v), 60)
                h2, m2 = divmod(m2, 60)
                return f"{h2}h{m2:02d}m{s2:02d}s" if h2 else f"{m2}m{s2:02d}s"

            ttfp_str   = fmt_s(d.get("ttfp_s"))
            load_str   = fmt_s(d.get("load_time_s"))
            spp        = d.get("spp", "—")
            max_samp   = d.get("max_samples", "—")
            mode_str   = d.get("mode", "—") or "—"

            timings_html = (
                '<div class="dp-section">'
                '<div class="dp-section-title">Timings</div>'
                '<div class="dp-grid">'
                f'<div class="dp-kv"><span class="dp-k">Chargement USD</span><span class="dp-v">{load_str}</span></div>'
                f'<div class="dp-kv"><span class="dp-k">First Pixel</span><span class="dp-v">{ttfp_str}</span></div>'
                f'<div class="dp-kv"><span class="dp-k">Mode</span><span class="dp-v">{escape(str(mode_str))}</span></div>'
                f'<div class="dp-kv"><span class="dp-k">SPP</span><span class="dp-v">{spp}</span></div>'
                f'<div class="dp-kv"><span class="dp-k">Max samples</span><span class="dp-v">{max_samp}</span></div>'
                '</div>'
                '</div>'
            )

            # ── GPU Memory ───────────────────────────────────────────────
            def stacked_bar(geo, tex, vol, other, vram_cap, used_total):
                """
                Barre stackée Geo/Tex/Vol/Autre.
                - vram_cap  : capacité réelle de la carte (None si inconnue)
                - used_total: valeur totale à afficher (current ou peak)
                La largeur 100% représente vram_cap si connu, sinon used_total.
                Si used_total > vram_cap, la portion qui dépasse est en rouge.
                """
                total = geo + tex + vol + other
                if total <= 0 and used_total <= 0:
                    return ""
                ref = vram_cap if vram_cap else max(used_total, total)
                if ref <= 0:
                    return ""
                def pct(v): return min(v / ref * 100, 100)
                overflow_pct = max((used_total - ref) / ref * 100, 0) if vram_cap else 0
                cap_str = f" / {vram_cap:.0f} GB" if vram_cap else " GB"
                lbl_cls = "mem-bar-lbl-over" if vram_cap and used_total > vram_cap else "mem-bar-lbl"
                title_str = f"Geo:{geo:.2f} Tex:{tex:.2f} Vol:{vol:.2f} Autre:{other:.2f} GB"
                overflow_seg = (
                    f'<div class="mb-overflow" style="width:{overflow_pct:.1f}%"></div>'
                    if overflow_pct > 0 else ""
                )
                return (
                    f'<div class="mem-bar-wrap" title="{title_str}">'
                    '<div class="mem-bar">'
                    f'<div class="mb-geo"   style="width:{pct(geo):.1f}%"></div>'
                    f'<div class="mb-tex"   style="width:{pct(tex):.1f}%"></div>'
                    f'<div class="mb-vol"   style="width:{pct(vol):.1f}%"></div>'
                    f'<div class="mb-other" style="width:{pct(other):.1f}%"></div>'
                    f'{overflow_seg}'
                    '</div>'
                    f'<span class="{lbl_cls}">{used_total:.2f}{cap_str}</span>'
                    '</div>'
                )

            gpu_mem_html = ""
            for dv in d.get("devices", []):
                is_gpu = dv.get("type", "").lower() not in ("embreecpu", "cpu", "software")
                if not is_gpu:
                    continue
                cur_total   = dv.get("used_gb",  0)
                peak_total  = dv.get("peak_gb",  0)
                host_cur    = dv.get("host_gb",      0)
                host_peak   = dv.get("peak_host_gb", 0)
                vram_cap    = _lookup_vram_gb(dv.get("label", ""))

                overflow    = vram_cap is not None and peak_total > vram_cap
                if overflow:
                    overflow_badge = (
                        f' <span class="overflow-badge">&#9888; peak +{peak_total - vram_cap:.1f} GB'
                        f' au-dela de {vram_cap:.0f} GB VRAM</span>'
                    )
                elif vram_cap is None:
                    overflow_badge = ' <span class="overflow-badge-unknown">GPU non repertorie dans config.json</span>'
                else:
                    overflow_badge = ""

                bar_cur  = stacked_bar(
                    dv["geo_gb"],      dv["tex_gb"],      dv["vol_gb"],      dv["other_gb"],
                    vram_cap, cur_total
                )
                bar_peak = stacked_bar(
                    dv["peak_geo_gb"], dv["peak_tex_gb"], dv["peak_vol_gb"], dv["peak_other_gb"],
                    vram_cap, peak_total
                )

                # Tooltip explicatif pour RAM host
                host_tip = "Portion du device-memory physiquement en RAM systeme (CUDA Unified Memory via PCIe)"
                dv_label_esc = escape(dv['label'])
                gpu_mem_html += (
                    '<div class="dv-block">'
                    f'<div class="dv-title">{dv_label_esc}{overflow_badge}</div>'
                    f'<div class="dv-row"><span class="dv-lbl" title="Memoire allouee en fin de frame">Current</span>{bar_cur}</div>'
                    f'<div class="dv-row"><span class="dv-lbl" title="Maximum atteint pendant le rendu">Peak</span>{bar_peak}</div>'
                    f'<div class="dv-row"><span class="dv-lbl" title="{host_tip}">RAM host</span>'
                    f'<span class="dv-val mono">cur {host_cur:.2f} GB &nbsp;/&nbsp; peak {host_peak:.2f} GB</span></div>'
                    '<div class="mem-legend">'
                    '<span class="leg-geo">&#9632; Geometrie</span>'
                    '<span class="leg-tex">&#9632; Textures</span>'
                    '<span class="leg-vol">&#9632; Volumes</span>'
                    '<span class="leg-other">&#9632; Autre</span>'
                    '<span class="leg-overflow">&#9632; Depassement VRAM</span>'
                    '</div>'
                    '</div>'
                )

            # ── RAM système ──────────────────────────────────────────────
            sys_cur   = d.get("sys_mem_current_gb", 0)
            sys_peak  = d.get("sys_mem_peak_gb",    0)
            sys_total = d.get("sys_mem_total_gb",   0)
            # sys_total dans Karma = budget interne Karma, pas la RAM machine totale.
            # On n'affiche pas de % si peak > total (résultat absurde > 100%).
            ram_reliable = sys_total > 0 and sys_peak <= sys_total * 1.02
            if ram_reliable:
                sys_pct   = sys_peak / sys_total * 100
                fill_w    = f"{sys_pct:.1f}%"
                ram_lbl   = f"Peak {sys_peak:.1f} GB / {sys_total:.1f} GB ({sys_pct:.0f}%)"
            else:
                fill_w    = "100%"
                ram_lbl   = (
                    f"Peak {sys_peak:.1f} GB"
                    + (f" (budget Karma : {sys_total:.1f} GB)" if sys_total > 0 else "")
                )
            ram_html  = (
                '<div class="dp-section">'
                '<div class="dp-section-title">RAM Process</div>'
                '<div class="ram-note">RAM utilisee par le process Karma (RSS)</div>'
                '<div class="ram-bar-wrap">'
                '<div class="ram-bar">'
                f'<div class="ram-bar-fill" style="width:{fill_w}"></div>'
                '</div>'
                f'<span class="ram-lbl">{ram_lbl}</span>'
                '</div>'
                '</div>'
            )

            # ── GPU Memory section ───────────────────────────────────────
            if d.get("devices"):
                no_gpu_msg = "<span class='dp-na'>Aucune donnee GPU</span>"
                gpu_section = (
                    '<div class="dp-section">'
                    '<div class="dp-section-title">Memoire GPU</div>'
                    + (gpu_mem_html if gpu_mem_html else no_gpu_msg) +
                    '</div>'
                )
            else:
                gpu_section = ""

            # ── Scène / Géométrie ────────────────────────────────────────
            def fmt_num(v):
                if v is None or v == 0: return "—"
                if v >= 1_000_000_000: return f"{v/1_000_000_000:.1f}B"
                if v >= 1_000_000:    return f"{v/1_000_000:.1f}M"
                if v >= 1_000:        return f"{v/1_000:.1f}k"
                return str(v)

            geo_poly_total  = fmt_num(d.get("geo_polygon_total"))
            geo_poly_unique = fmt_num(d.get("geo_polygon_unique"))
            geo_curve       = fmt_num(d.get("geo_curve_total"))
            geo_diced       = fmt_num(d.get("geo_diced_polys"))
            rays_total      = fmt_num(d.get("rays_total"))
            rays_primary    = fmt_num(d.get("rays_primary"))
            rays_occlusion  = fmt_num(d.get("rays_occlusion"))

            scene_html = (
                '<div class="dp-section">'
                '<div class="dp-section-title">Scene</div>'
                '<div class="dp-grid">'
                f'<div class="dp-kv"><span class="dp-k">Polygones</span><span class="dp-v">{geo_poly_total} <span class="dp-sub">({geo_poly_unique} uniques)</span></span></div>'
                f'<div class="dp-kv"><span class="dp-k">Curves</span><span class="dp-v">{geo_curve}</span></div>'
                f'<div class="dp-kv"><span class="dp-k">Diced polys</span><span class="dp-v">{geo_diced}</span></div>'
                f'<div class="dp-kv"><span class="dp-k">Rays total</span><span class="dp-v">{rays_total}</span></div>'
                f'<div class="dp-kv"><span class="dp-k">Rays primary</span><span class="dp-v">{rays_primary}</span></div>'
                f'<div class="dp-kv"><span class="dp-k">Rays occlusion</span><span class="dp-v">{rays_occlusion}</span></div>'
                '</div>'
                '</div>'
            )

            # ── Textures ─────────────────────────────────────────────────
            tex_missing = d.get("tex_missing", 0)
            if tex_missing:
                missing_s = "s" if tex_missing > 1 else ""
                missing_badge = f' <span class="overflow-badge">&#9888; {tex_missing} manquante{missing_s}</span>'
            else:
                missing_badge = ""
            tex_unique       = d.get("tex_unique", "—")
            tex_disk_gb      = d.get("tex_disk_gb", 0)
            tex_uncomp_gb    = d.get("tex_uncompressed_gb", 0)
            aov_peak_gb      = d.get("aov_peak_gb", 0)

            tex_html = (
                '<div class="dp-section">'
                f'<div class="dp-section-title">Textures{missing_badge}</div>'
                '<div class="dp-grid">'
                f'<div class="dp-kv"><span class="dp-k">Fichiers uniques</span><span class="dp-v">{tex_unique}</span></div>'
                f'<div class="dp-kv"><span class="dp-k">Taille disque</span><span class="dp-v">{tex_disk_gb:.2f} GB</span></div>'
                f'<div class="dp-kv"><span class="dp-k">Decompresse</span><span class="dp-v">{tex_uncomp_gb:.2f} GB</span></div>'
                f'<div class="dp-kv"><span class="dp-k">AOV buffers</span><span class="dp-v">{aov_peak_gb:.2f} GB</span></div>'
                '</div>'
                '</div>'
            )

            frame_rows += (
                f'\n        <tr class="detail-row" id="detail-{idx}" style="display:none">'
                '\n          <td colspan="10">'
                '\n            <div class="detail-panel">'
                f'\n              {timings_html}'
                f'\n              {gpu_section}'
                f'\n              {ram_html}'
                f'\n              {scene_html}'
                f'\n              {tex_html}'
                '\n            </div>'
                '\n          </td>'
                '\n        </tr>'
            )

    # ── HTML final ───────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EXR Analyzer — {escape(seq_name)}</title>
<style>
/* ── Reset & base ── */
*, *::before, *::after {{ box-sizing: border-box; margin:0; padding:0; }}
body {{
  font-family: 'Segoe UI', system-ui, sans-serif;
  background: #0d1117;
  color: #c9d1d9;
  font-size: 14px;
  line-height: 1.5;
}}
a {{ color: #58a6ff; }}

/* ── Layout ── */
.page {{ max-width: 1400px; margin: 0 auto; padding: 32px 24px; }}

/* ── Header ── */
.report-header {{
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 32px; flex-wrap: wrap; gap: 12px;
}}
.report-title {{ font-size: 1.5rem; font-weight: 700; color: #f0f6fc; }}
.report-title span {{ color: #7c3aed; }}
.report-meta {{ font-size: .82rem; color: #6e7681; margin-top: 4px; }}
.report-meta b {{ color: #c9d1d9; }}
.threshold-badge {{
  background: #21262d; border: 1px solid #30363d;
  border-radius: 6px; padding: 6px 14px; font-size: .82rem;
  color: #c9d1d9; white-space: nowrap;
}}
.threshold-badge b {{ color: #f97316; }}

/* ── Summary cards ── */
.summary {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 36px; }}
.scard {{
  background: #161b22; border: 1px solid #30363d;
  border-radius: 10px; padding: 18px 24px; flex: 1; min-width: 130px;
}}
.scard .snum {{ font-size: 2.2rem; font-weight: 700; line-height: 1; }}
.scard .slbl {{ font-size: .75rem; color: #6e7681; text-transform: uppercase;
                letter-spacing: .08em; margin-top: 4px; }}
.scard .spct {{ font-size: .8rem; color: #6e7681; margin-top: 2px; }}
.c-ok   {{ color: #3fb950; border-top: 3px solid #3fb950; }}
.c-hot  {{ color: #f97316; border-top: 3px solid #f97316; }}
.c-err  {{ color: #f85149; border-top: 3px solid #f85149; }}
.c-tot  {{ color: #79c0ff; border-top: 3px solid #79c0ff; }}
.c-xpu  {{ border-top: 3px solid #a371f7; }}
.xpu-global-bar {{
  height: 12px; border-radius: 6px; overflow: hidden;
  background: #21262d; display: flex; margin-bottom: 6px;
}}
.xpu-global-gpu {{ background: #3fb950; height: 100%; }}
.xpu-global-cpu {{ background: #388bfd; height: 100%; }}
.xpu-global-labels {{ display: flex; justify-content: space-between; font-size: .82rem; font-weight: 600; }}

/* ── Section title ── */
.section-title {{
  font-size: .75rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: .1em; color: #6e7681;
  margin-bottom: 16px; padding-bottom: 8px;
  border-bottom: 1px solid #21262d;
}}

/* ── Machine cards ── */
.machines {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
             gap: 16px; margin-bottom: 40px; }}
.mc {{
  background: #161b22; border: 1px solid #30363d;
  border-radius: 10px; overflow: hidden;
}}
.mc-header {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; background: #1c2128; gap: 12px; flex-wrap: wrap;
  border-bottom: 1px solid #30363d;
}}
.mc-title {{ display: flex; align-items: center; gap: 8px; }}
.host-icon {{ font-size: 1.1rem; }}
.host-name {{ font-weight: 600; color: #f0f6fc; font-size: .95rem; }}
.mc-mode-badge {{
  font-size: .7rem; padding: 2px 8px; border-radius: 999px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .05em;
}}
.mode-hybrid  {{ background: #2d2006; color: #f97316; border: 1px solid #78350f; }}
.mode-gpu     {{ background: #0d2d1a; color: #3fb950; border: 1px solid #1a4731; }}
.mode-cpu     {{ background: #0d1f3c; color: #79c0ff; border: 1px solid #1a3a6e; }}
.mode-unknown {{ background: #21262d; color: #6e7681; border: 1px solid #30363d; }}

.mc-stats {{ display: flex; gap: 12px; font-size: .78rem; flex-wrap: wrap; }}
.stat-ok  {{ color: #3fb950; }}
.stat-hot {{ color: #f97316; font-weight: 600; }}
.stat-err {{ color: #f85149; }}
.stat-total {{ color: #6e7681; }}

.mc-body {{ padding: 16px 18px; display: flex; gap: 24px; flex-wrap: wrap; }}
.mc-info {{ flex: 1; min-width: 220px; display: flex; flex-direction: column; gap: 10px; }}
.info-row {{ display: flex; align-items: flex-start; gap: 10px; }}
.info-lbl {{ font-size: .72rem; color: #6e7681; text-transform: uppercase;
              letter-spacing: .05em; width: 70px; flex-shrink: 0; padding-top: 2px; }}
.info-val {{ font-size: .85rem; color: #c9d1d9; word-break: break-word; }}
.gpu-val  {{ color: #3fb950; font-weight: 500; }}

/* Ratio bar */
.ratio-wrap {{ flex: 1; }}
.ratio-label {{ display: flex; gap: 6px; margin-bottom: 5px; flex-wrap: wrap; }}
.badge {{
  font-size: .7rem; padding: 1px 7px; border-radius: 999px;
  font-weight: 600;
}}
.badge.gpu {{ background: #0d2d1a; color: #3fb950; border: 1px solid #1a4731; }}
.badge.cpu {{ background: #0d1f3c; color: #79c0ff; border: 1px solid #1a3a6e; }}
.ratio-bar {{
  height: 8px; border-radius: 4px; overflow: hidden;
  background: #21262d; display: flex;
}}
.ratio-fill-gpu {{ background: #3fb950; height: 100%; }}
.ratio-fill-cpu {{ background: #388bfd; height: 100%; }}

/* Error rate bar */
.err-rate-wrap {{ display: flex; align-items: center; gap: 8px; flex: 1; }}
.err-rate-bar  {{ flex: 1; height: 6px; background: #21262d; border-radius: 3px; overflow: hidden; }}
.err-rate-fill {{ height: 100%; background: #f97316; border-radius: 3px; transition: width .3s; }}
.err-rate-val  {{ font-size: .8rem; color: #f97316; font-weight: 600; min-width: 36px; }}

/* Devices table */
.dev-table {{
  flex: 1; min-width: 260px; border-collapse: collapse; font-size: .78rem;
  align-self: flex-start;
}}
.dev-table th {{
  padding: 5px 10px; text-align: left; color: #6e7681;
  font-weight: 600; text-transform: uppercase; font-size: .68rem;
  border-bottom: 1px solid #30363d; letter-spacing: .05em;
}}
.dev-table td {{ padding: 5px 10px; border-bottom: 1px solid #21262d; }}
.dev-gpu td:first-child {{ color: #3fb950; }}
.dev-cpu td:first-child {{ color: #79c0ff; }}
.dev-bar {{ height: 4px; background: #21262d; border-radius: 2px; overflow: hidden; margin-top: 3px; width: 60px; }}
.dev-bar-fill.gpu {{ background: #3fb950; height: 100%; }}
.dev-bar-fill.cpu {{ background: #388bfd; height: 100%; }}

/* Sparkline */
.spark {{
  padding: 8px 18px 12px; display: flex; flex-wrap: wrap; gap: 2px;
  border-top: 1px solid #21262d;
}}
.spark span {{
  display: inline-block; width: 7px; height: 7px; border-radius: 1px; cursor: default;
}}
.sp-ok  {{ background: #1f4a2a; }}
.sp-hot {{ background: #f97316; }}
.sp-err {{ background: #f85149; }}

/* ── Filter bar ── */
.filter-bar {{
  display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; align-items: center;
}}
.filter-btn {{
  background: #21262d; border: 1px solid #30363d; color: #c9d1d9;
  padding: 5px 14px; border-radius: 6px; cursor: pointer; font-size: .82rem;
  transition: all .15s;
}}
.filter-btn:hover {{ border-color: #58a6ff; color: #58a6ff; }}
.filter-btn.active {{ background: #1a3a6e; border-color: #388bfd; color: #79c0ff; font-weight: 600; }}
.filter-count {{ font-size: .75rem; color: #6e7681; margin-left: auto; }}

/* ── Frames table ── */
.table-wrap {{ overflow-x: auto; }}
table.frames-table {{
  width: 100%; border-collapse: collapse; font-size: .83rem;
}}
.frames-table thead th {{
  background: #161b22; color: #6e7681; padding: 9px 12px;
  text-align: left; font-weight: 600; font-size: .72rem;
  text-transform: uppercase; letter-spacing: .06em;
  position: sticky; top: 0; z-index: 1;
  border-bottom: 2px solid #30363d;
}}
.frames-table tbody tr {{ transition: background .1s; }}
.frames-table tbody tr:hover {{ background: #1c2128 !important; }}
.frames-table td {{ padding: 7px 12px; border-bottom: 1px solid #21262d; }}

.tr-ok  {{ background: transparent; }}
.tr-hot {{ background: rgba(249,115,22,.07); }}
.tr-err {{ background: rgba(248,81,73,.07); }}

.td-frame {{ color: #6e7681; font-size: .78rem; width: 60px; }}
.td-file  {{ color: #8b949e; font-size: .78rem; max-width: 280px; word-break: break-all; }}
.td-host  {{ color: #c9d1d9; font-size: .82rem; }}

.pill {{
  display: inline-block; padding: 2px 8px; border-radius: 999px;
  font-size: .72rem; font-weight: 600;
}}
.pill-ok  {{ background: #0d2d1a; color: #3fb950; }}
.pill-hot {{ background: #2d1505; color: #f97316; }}
.pill-err {{ background: #2d0f0e; color: #f85149; }}

.mono {{ font-family: 'Consolas', monospace; }}
.val-hot {{ color: #f97316 !important; font-weight: 600; }}
.err-msg {{ display: block; font-size: .72rem; color: #f85149; margin-top: 2px; }}

/* Device tags in frames table */
.td-device {{ max-width: 220px; }}
.dev-tag {{
  display: inline-block; font-size: .72rem; padding: 2px 7px;
  border-radius: 4px; font-family: 'Consolas', monospace;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px;
}}
.gpu-tag {{ background: #0d2d1a; color: #3fb950; border: 1px solid #1a4731; }}
.cpu-tag {{ background: #0d1f3c; color: #79c0ff; border: 1px solid #1a3a6e; }}
.unk-tag {{ background: #21262d; color: #6e7681; border: 1px solid #30363d; }}

/* Ratio mini dans le tableau frames */
.td-ratio {{ width: 110px; }}
.ratio-mini {{ display: flex; flex-direction: column; gap: 3px; }}
.ratio-mini-bar {{
  height: 4px; border-radius: 2px; background: #21262d; overflow: hidden; width: 80px;
}}
.ratio-mini-gpu {{ height: 100%; background: #3fb950; }}
.ratio-mini-lbl {{ font-size: .7rem; font-family: 'Consolas', monospace; }}
.ratio-mini-na  {{ color: #6e7681; font-size: .8rem; }}
.c-gpu {{ color: #3fb950; }}
.c-cpu {{ color: #79c0ff; }}
.td-render {{ color: #c9d1d9; width: 72px; font-size: .78rem; }}
.td-mem    {{ color: #8b949e; width: 72px; font-size: .78rem; }}
.td-max    {{ width: 90px; }}

/* ── Expand icon ── */
.expand-icon {{ font-size:10px; color:#58a6ff; margin-left:4px; transition:transform .2s; display:inline-block; }}
.expand-icon.open {{ transform: rotate(90deg); }}

/* ── Detail row ── */
.detail-row td {{ padding:0 !important; border:none !important; }}
.detail-panel {{
  background: #131920;
  border: 1px solid #2d3a4a;
  border-radius: 8px;
  margin: 4px 8px 8px 8px;
  padding: 16px 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}}
.dp-section {{
  flex: 1 1 280px;
  min-width: 240px;
}}
.dp-section-title {{
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: #8b949e;
  margin-bottom: 10px;
  padding-bottom: 4px;
  border-bottom: 1px solid #21262d;
}}
.dp-grid {{ display: flex; flex-direction: column; gap: 5px; }}
.dp-kv {{ display: flex; justify-content: space-between; align-items: baseline; font-size: 13px; }}
.dp-k {{ color: #8b949e; }}
.dp-v {{ color: #e6edf3; font-weight: 500; }}
.dp-sub {{ color: #6e7681; font-size: 11px; font-weight: 400; }}
.dp-na {{ color: #6e7681; font-style: italic; font-size: 12px; }}

/* ── RAM bar ── */
.ram-bar-wrap {{ display: flex; flex-direction: column; gap: 4px; }}
.ram-bar {{ height: 8px; background: #21262d; border-radius: 4px; overflow: hidden; }}
.ram-bar-fill {{ height: 100%; background: #388bfd; border-radius: 4px; transition: width .3s; }}
.ram-lbl {{ font-size: 12px; color: #8b949e; }}

/* ── GPU memory stacked bar ── */
.dv-block {{ margin-bottom: 12px; }}
.dv-title {{ font-size: 12px; font-weight: 600; color: #e6edf3; margin-bottom: 6px; }}
.dv-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }}
.dv-lbl {{ font-size: 11px; color: #6e7681; width: 52px; flex-shrink: 0; }}
.dv-val {{ font-size: 12px; color: #c9d1d9; }}
.mem-bar-wrap {{ display: flex; align-items: center; gap: 8px; flex: 1; }}
.mem-bar {{ height: 10px; background: #21262d; border-radius: 4px; overflow: hidden; display: flex; flex: 1; }}
.mb-geo   {{ background: #388bfd; height: 100%; }}
.mb-tex   {{ background: #f0883e; height: 100%; }}
.mb-vol   {{ background: #a371f7; height: 100%; }}
.mb-other {{ background: #6e7681; height: 100%; }}
.mem-bar-lbl {{ font-size: 11px; color: #8b949e; white-space: nowrap; min-width: 55px; }}
.mem-legend {{ display: flex; gap: 10px; margin-top: 4px; flex-wrap: wrap; }}
.mem-legend span {{ font-size: 10px; }}
.leg-geo      {{ color: #388bfd; }}
.leg-tex      {{ color: #f0883e; }}
.leg-vol      {{ color: #a371f7; }}
.leg-other    {{ color: #6e7681; }}
.leg-overflow {{ color: #f85149; }}
.mb-overflow  {{ background: #f85149; height: 100%; }}
.mem-bar-lbl-over {{ font-size: 11px; color: #f85149; white-space: nowrap; min-width: 55px; font-weight: 600; }}
.ram-note {{ font-size: 11px; color: #6e7681; font-style: italic; margin-bottom: 6px; }}

/* ── Badges ── */
.overflow-badge {{
  display: inline-block;
  background: rgba(240,136,62,.2);
  color: #f0883e;
  border: 1px solid rgba(240,136,62,.4);
  border-radius: 4px;
  font-size: 10px;
  padding: 1px 6px;
  margin-left: 6px;
  font-weight: 500;
}}
.overflow-badge-unknown {{
  display: inline-block;
  background: rgba(110,118,129,.15);
  color: #6e7681;
  border: 1px solid rgba(110,118,129,.3);
  border-radius: 4px;
  font-size: 10px;
  padding: 1px 6px;
  margin-left: 6px;
}}
</style>
</head>
<body>
<div class="page">

  <!-- Header -->
  <div class="report-header">
    <div>
      <div class="report-title">EXR Analyzer <span>Report</span></div>
      <div class="report-meta">
        Séquence&nbsp;<b>{escape(seq_name)}</b> &nbsp;·&nbsp;
        {total} frame{"s" if total!=1 else ""} &nbsp;·&nbsp;
        Généré le&nbsp;<b>{gen_date}</b>
      </div>
    </div>
    <div class="threshold-badge">Seuil de détection &gt; <b>{threshold}</b></div>
  </div>

  <!-- Summary cards -->
  <div class="summary">
    <div class="scard c-tot">
      <div class="snum">{total}</div>
      <div class="slbl">Frames analysées</div>
    </div>
    <div class="scard c-ok">
      <div class="snum">{ok}</div>
      <div class="slbl">OK</div>
      <div class="spct">{f"{ok/total*100:.1f}" if total else "0"}%</div>
    </div>
    <div class="scard c-hot">
      <div class="snum">{len(hotspot)}</div>
      <div class="slbl">Pixels excessifs</div>
      <div class="spct">{hot_pct}% des frames</div>
    </div>
    <div class="scard c-err">
      <div class="snum">{len(errors)}</div>
      <div class="slbl">Erreurs</div>
      <div class="spct">{err_pct}% des frames</div>
    </div>
    {xpu_global_card}
  </div>

  <!-- Frames table -->
  <div class="section-title">Détail par frame</div>
  <div class="filter-bar">
    <button class="filter-btn active" onclick="filterTable('all')">Toutes</button>
    <button class="filter-btn" onclick="filterTable('hot')">⚠ Hotspots ({len(hotspot)})</button>
    <button class="filter-btn" onclick="filterTable('err')">✗ Erreurs ({len(errors)})</button>
    <span class="filter-count" id="count-label">{total} frame{"s" if total!=1 else ""} affichée{"s" if total!=1 else ""}</span>
  </div>
  <div class="table-wrap">
    <table class="frames-table" id="frames-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Fichier</th>
          <th>Machine</th>
          <th>Device</th>
          <th>Ratio XPU</th>
          <th>Statut</th>
          <th>Render</th>
          <th>Mém.</th>
          <th>VRAM</th>
          <th>Max</th>
        </tr>
      </thead>
      <tbody>
        {frame_rows}
      </tbody>
    </table>
  </div>

  <!-- Machines -->
  <div class="section-title" style="margin-top:40px">Machines ({len(machines)})</div>
  <div class="machines">
    {machine_cards_html}
  </div>

</div>

<script>
function filterTable(filter) {{
  const rows = document.querySelectorAll('#frames-table tbody tr[data-status]');
  let visible = 0;
  rows.forEach(row => {{
    const status = row.dataset.status;
    const show = filter === 'all' || status === filter;
    row.style.display = show ? '' : 'none';
    if (show) visible++;
    // Masquer aussi la detail-row si la frame est cachée
    const onclickAttr = row.getAttribute('onclick');
    if (onclickAttr) {{
      const m = onclickAttr.match(/\\d+/);
      if (m) {{
        const dr = document.getElementById('detail-' + m[0]);
        if (dr && !show) dr.style.display = 'none';
      }}
    }}
  }});
  document.getElementById('count-label').textContent =
    visible + ' frame' + (visible !== 1 ? 's' : '') + ' affichée' + (visible !== 1 ? 's' : '');
  document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
  event.target.classList.add('active');
}}

function toggleDetail(idx) {{
  const dr   = document.getElementById('detail-' + idx);
  const icon = document.getElementById('icon-' + idx);
  if (!dr) return;
  const open = dr.style.display === 'none' || dr.style.display === '';
  dr.style.display = open ? 'table-row' : 'none';
  if (icon) icon.classList.toggle('open', open);
}}
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  HTML exporté → {output_path}")


# ──────────────────────────────────────────────
#  Mode diagnostic
# ──────────────────────────────────────────────

def _debug_inspect(path: str):
    """Affiche les canaux, métadonnées et statistiques pixel brutes d'un EXR."""
    files = collect_exr_files(path)
    if not files:
        print(f"[DEBUG] Aucun fichier EXR trouvé : {path}")
        return

    for filepath in files:
        print(f"\n{'─'*60}")
        print(f"  Fichier : {filepath}")
        print(f"{'─'*60}")
        try:
            exr, header, channels = _open_exr(filepath)

            # Métadonnées brutes (toutes les clés)
            print(f"\n  [HEADER — {len(header)} clé(s)]")
            for k, v in sorted(header.items()):
                val_str = str(v)
                if len(val_str) > 80:
                    val_str = val_str[:77] + "..."
                print(f"    {k!r:40s} = {val_str}")

            # Canaux et stats
            print(f"\n  [CANAUX — {len(channels)} canal(aux)]")
            for ch_name in sorted(channels):
                arr = _read_channel(exr, ch_name, header)
                if arr is None:
                    print(f"    {ch_name:30s}  [lecture impossible]")
                    continue
                # Filtrer NaN/Inf pour les stats
                finite = arr[np.isfinite(arr)]
                nan_count = int(np.sum(np.isnan(arr)))
                inf_count = int(np.sum(np.isinf(arr)))
                if finite.size > 0:
                    mn, mx, mean = float(np.min(finite)), float(np.max(finite)), float(np.mean(finite))
                    above_5  = int(np.sum(finite > 5.0))
                    above_1  = int(np.sum(finite > 1.0))
                    print(f"    {ch_name:30s}  min={mn:10.4f}  max={mx:10.4f}  "
                          f"mean={mean:8.4f}  >1.0: {above_1:6d}px  >5.0: {above_5:6d}px"
                          + (f"  NaN:{nan_count}" if nan_count else "")
                          + (f"  Inf:{inf_count}" if inf_count else ""))
                else:
                    print(f"    {ch_name:30s}  [tous NaN/Inf — NaN:{nan_count} Inf:{inf_count}]")

            if hasattr(exr, "close"):
                exr.close()
        except Exception as e:
            print(f"  [ERREUR] {e}")


# ──────────────────────────────────────────────
#  Point d'entrée
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Analyse une séquence EXR : métadonnées machine et pixels excessifs."
    )
    parser.add_argument("path",
        help="Chemin vers un fichier EXR, un dossier, ou un glob (ex: /seq/render.*.exr)")
    parser.add_argument("-t", "--threshold", type=float,
        default=float(_CONFIG.get("threshold", 5.0)),
        help="Seuil de valeur de pixel (défaut : config.json ou 5.0)")
    default_jobs = min(os.cpu_count() or 4, 16)
    parser.add_argument("-j", "--jobs", type=int, default=default_jobs,
        help=f"Nombre de workers parallèles (défaut : {default_jobs} = cpu_count)")
    parser.add_argument("--csv",  metavar="FILE", help="Exporter les résultats en CSV")
    parser.add_argument("--json", metavar="FILE", help="Exporter les résultats en JSON")
    parser.add_argument("--html", metavar="FILE", nargs="?", const="",
        help="Exporter les résultats en HTML (optionnel : chemin du fichier)")
    parser.add_argument("--no-browser", action="store_true", help="Ne pas ouvrir le rapport HTML dans le navigateur")
    parser.add_argument("--quiet", action="store_true", help="Affichage minimal")
    parser.add_argument("--debug", action="store_true",
        help="Dump les canaux et valeurs min/max de chaque frame (diagnostic)")

    args = parser.parse_args()

    # Mode debug : inspecter les canaux et valeurs brutes
    if args.debug:
        _debug_inspect(args.path)
        sys.exit(0)

    # Collecter les fichiers
    files = collect_exr_files(args.path)
    if not files:
        print(f"[ERREUR] Aucun fichier EXR trouvé pour : {args.path}")
        sys.exit(1)

    if not args.quiet:
        print(f"\n  {len(files)} fichier(s) EXR détecté(s). Analyse en cours…")

    # Analyser en parallèle avec des threads
    # Le GIL est relâché par les extensions C (numpy + OpenEXR) pendant la décompression
    # et les opérations pixel → ThreadPoolExecutor parallélise vraiment le travail
    # ProcessPoolExecutor serait pire sur Windows (overhead spawn 1-3s/worker)
    results: list[FrameResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = {
            executor.submit(analyze_frame, f, args.threshold): f
            for f in files
        }
        done = 0
        for future in concurrent.futures.as_completed(futures):
            done += 1
            result = future.result()
            results.append(result)
            if not args.quiet:
                marker = "⚠" if result.has_excessive_pixels else ("✗" if result.error else "✓")
                print(f"  [{done:>4}/{len(files)}] {marker}  {Path(result.filepath).name}", end="\r")

    if not args.quiet:
        print(" " * 80, end="\r")  # effacer la ligne de progression

    # Trier par numéro de frame
    results.sort(key=lambda r: r.frame_number if r.frame_number is not None else -1)

    # Affichage console
    if not args.quiet:
        print_summary(results, args.threshold)

    # Exports
    if args.csv:
        export_csv(results, args.csv)
    if args.json:
        export_json(results, args.json)

    # HTML : toujours généré (auto si pas de chemin précisé)
    if args.html is not None:
        html_path = args.html if args.html else None
    else:
        html_path = None  # --html non passé → on génère quand même par défaut

    # Chemin par défaut : même dossier que la séquence, nom basé sur le nom EXR + timestamp
    if html_path is None or html_path == "":
        import datetime, re
        seq_dir  = Path(results[0].filepath).parent if results else Path(".")
        # Nom de base = stem du premier fichier sans le numéro de frame final
        raw_stem = Path(results[0].filepath).stem          # ex: "render.0001"
        seq_stem = re.sub(r'[._-]?\d+$', '', raw_stem)    # → "render"
        if not seq_stem:
            seq_stem = raw_stem
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = str(seq_dir / f"{seq_stem}_{ts}.html")

    export_html(results, html_path, args.threshold)

    # Ouvrir dans le navigateur par défaut (sauf si --no-browser)
    if not args.no_browser:
        import webbrowser
        webbrowser.open(Path(html_path).resolve().as_uri())

    # Code de sortie : 1 si des frames problématiques trouvées
    has_issues = any(r.has_excessive_pixels or r.error for r in results)
    sys.exit(1 if has_issues else 0)


if __name__ == "__main__":
    main()
