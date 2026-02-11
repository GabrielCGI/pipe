import sys
import re
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple, List

VERSION_RE = re.compile(r"^v(\d{3,})$", re.IGNORECASE)

SEVEN_ZIP_EXE = r"C:\Program Files\7-Zip\7z.exe"
FLAME_ROOT = Path(r"I:\VCA_Perlee_2510\08_Flame")

def find_latest_version_dir(parent: Path) -> Optional[Path]:
    if not parent.exists() or not parent.is_dir():
        return None

    best = (-1, None)
    for child in parent.iterdir():
        if not child.is_dir():
            continue
        m = VERSION_RE.match(child.name)
        if not m:
            continue
        vnum = int(m.group(1))
        if vnum > best[0]:
            best = (vnum, child)

    return best[1]

def get_latest_flame_dirs(root_dir: Path) -> Dict[str, Path]:
    targets = {
        "toFlame_beauty": root_dir / "toFlame_beauty",
        "toFlame_cryptos": root_dir / "toFlame_cryptos",
    }

    out = {}
    for name, folder in targets.items():
        latest = find_latest_version_dir(folder)
        if latest is None:
            raise RuntimeError(f"No v### folder found in {folder}")
        out[name] = latest

    return out

def extract_seq_shot_from_path(root_dir: Path) -> Tuple[str, str]:
    parts = list(root_dir.parts)
    lower = [p.lower() for p in parts]

    if "shots" not in lower:
        raise RuntimeError(f"Cannot find 'Shots' in path: {root_dir}")

    i = lower.index("shots")
    try:
        seq = parts[i + 1]
        shot = parts[i + 2]
    except IndexError:
        raise RuntimeError(f"Path does not contain sequence/shot after 'Shots': {root_dir}")

    return seq, shot

def build_7z_cmd(output_archive: str, sources: List[str]) -> List[str]:
    return [
        SEVEN_ZIP_EXE,
        "a",
        "-t7z",
        "-mx=0",     # store only (fast for EXR)
        "-v4g",      # split size
        output_archive,
        *sources,
    ]

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python zip_to_flame.py <input_2dRender_dir> <date_folder>")
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    date_folder = sys.argv[2]

    if not input_dir.exists():
        raise RuntimeError(f"Input directory does not exist: {input_dir}")

    print("Input dir:", input_dir)
    print("Date folder:", date_folder)

    seq, shot = extract_seq_shot_from_path(input_dir)

    latest = get_latest_flame_dirs(input_dir)
    sources = [str(latest["toFlame_beauty"]), str(latest["toFlame_cryptos"])]

    # Output path: I:\VCA_Perlee_2510\08_Flame\<DATE>\<SEQ>\<SHOT>\
    out_dir = FLAME_ROOT / date_folder / seq / shot
    out_dir.mkdir(parents=True, exist_ok=True)

    output_archive = str(out_dir / f"{shot}.7z")

    cmd = build_7z_cmd(output_archive, sources)

    print("Sequence:", seq)
    print("Shot:", shot)
    print("Output dir:", out_dir)
    print("Archive:", output_archive)
    print("Sources:")
    for s in sources:
        print("  ", s)

    print("\nRunning 7-Zip:")
    print(" ".join(shlex.quote(x) for x in cmd))

    subprocess.run(cmd, check=True)

    print("\nDONE.")

if __name__ == "__main__":
    main()
