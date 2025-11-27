import os
from pathlib import Path
from datetime import datetime
import ctypes  # for Windows MessageBox
import tempfile
import subprocess

# Root of production
ROOT = r"I:\VCA_Perlee_2510\03_Production\Shots"

# Sequence names to ignore entirely
SEQUENCE_FILTER = ["SANDBOX", "TURN"]

# Shot identifiers to ignore (format: "SEQ_SHOT", e.g.: "CAPS-03_SH0300")
SHOT_FILTER = [
    "CAPS-03_SH0300",
    "CAPS-03_SH0300A",
    # add more here
]


def get_latest_by_mtime(directory: Path, keyword: str):
    if not directory.exists():
        return None

    latest = None
    for child in directory.rglob("*.usda"):
        if keyword.lower() not in child.name.lower():
            continue
        try:
            mtime = child.stat().st_mtime
        except OSError:
            continue
        if latest is None or mtime > latest[0]:
            latest = (mtime, str(child))
    return latest


def fmt_time(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def open_in_notepad(text):
    try:
        fd, temp_path = tempfile.mkstemp(prefix="CFX_vs_ANIM_", suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        try:
            os.startfile(temp_path)  # type: ignore[attr-defined]
        except AttributeError:
            subprocess.Popen(["notepad", temp_path])
    except Exception as e:
        print(f"Failed to open Notepad: {e}")


def _build_output():
    root_path = Path(ROOT)

    older_cfx = []
    missing_cfx = []

    for seq in root_path.iterdir():

        if not seq.is_dir():
            continue

        # Filter sequences
        if any(filt.lower() in seq.name.lower() for filt in SEQUENCE_FILTER):
            continue

        for shot in seq.iterdir():
            if not shot.is_dir():
                continue

            # ----- Shot ignore logic (EXACT MATCH) -----
            shot_id = f"{seq.name}_{shot.name}".lower()
            ignored_ids = [s.lower() for s in SHOT_FILTER]
            if shot_id in ignored_ids:
                # Skip completely: no missing CFX, no older CFX checks
                continue
            # -------------------------------------------

            export = shot / "Export"
            cfx_dir = export / "_layer_cfx_master"
            anim_dir = export / "_layer_anm_master"

            latest_cfx = get_latest_by_mtime(cfx_dir, "cfx")
            latest_anim = get_latest_by_mtime(anim_dir, "anm")

            # Warn only if ANIM exists but CFX does not
            if latest_cfx is None and latest_anim is not None:
                missing_cfx.append(f"{seq.name}/{shot.name}")
                continue

            # CFX exists and ANIM exists → compare timestamps
            if latest_cfx and latest_anim:
                cfx_mtime, _ = latest_cfx
                anim_mtime, _ = latest_anim
                if cfx_mtime < anim_mtime:
                    older_cfx.append(f"{seq.name}/{shot.name}")

    # ----- Build output -----
    lines = []
    lines.append("=== CFX MASTER IS OLDER THAN ANIM ===")
    lines.append("")
    if older_cfx:
        lines.extend(older_cfx)
    else:
        lines.append("All good: no shots where CFX is older than ANIM.")
    lines.append("")
    lines.append("")

    lines.append("=== CFX DOES NOT EXIST YET (BUT ANIM EXISTS) ===")
    lines.append("")
    if missing_cfx:
        lines.extend(missing_cfx)
    else:
        lines.append("All good: no shots with missing CFX while ANIM exists.")
    lines.append("")
    lines.append("=== DONE ===")

    return "\n".join(lines)


def run():
    output = _build_output()
    print(output)
    open_in_notepad(output)

    try:
        ctypes.windll.user32.MessageBoxW(
            None,
            output,
            "CFX vs ANIM Check",
            0
        )
    except Exception:
        pass


def run_console():
    output = _build_output()
    print(output)
    open_in_notepad(output)
