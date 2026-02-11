import re
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple, List

VERSION_RE = re.compile(r"^v(\d{3,})$", re.IGNORECASE)

def find_latest_version_dir(parent: Path) -> Optional[Path]:
    if not parent.exists() or not parent.is_dir():
        return None

    best: Tuple[int, Optional[Path]] = (-1, None)
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

    out: Dict[str, Path] = {}
    for name, folder in targets.items():
        latest = find_latest_version_dir(folder)
        if latest is None:
            raise FileNotFoundError(f"Could not find any v### folder in: {folder}")
        out[name] = latest

    return out

def extract_seq_shot_from_path(root_dir: Path) -> Tuple[str, str]:
    """
    Attempts to find .../Shots/<SEQ>/<SHOT>/... in the path.
    Works for: I:\...\Shots\CAPS01\SH0130\Renders\2dRender
    """
    parts = [p for p in root_dir.parts]
    lower_parts = [p.lower() for p in parts]

    if "shots" not in lower_parts:
        raise ValueError(f"Could not find 'Shots' in path: {root_dir}")

    i = lower_parts.index("shots")
    try:
        seq = parts[i + 1]
        shot = parts[i + 2]
    except IndexError:
        raise ValueError(f"Path does not contain sequence/shot after 'Shots': {root_dir}")

    return seq, shot

def build_7z_split_command(
    seven_zip_exe: str,
    output_archive: str,
    source_dirs: List[str],
    volume_size: str = "4g",
    compression_level: int = 0,  # EXR: store is usually best
) -> List[str]:
    if not (0 <= compression_level <= 9):
        raise ValueError("compression_level must be 0..9")

    return [
        seven_zip_exe,
        "a",
        "-t7z",
        f"-mx={compression_level}",
        f"-v{volume_size}",
        output_archive,
        *source_dirs,
    ]

def main():
    root_dir = Path(r"I:\VCA_Perlee_2510\03_Production\Shots\CAPS01\SH0130\Renders\2dRender")
    out_root = Path(r"I:\VCA_Perlee_2510\08_Flame\260109")
    seven_zip_exe = r"C:\Program Files\7-Zip\7z.exe"

    seq, shot = extract_seq_shot_from_path(root_dir)

    latest = get_latest_flame_dirs(root_dir)
    sources = [str(latest["toFlame_beauty"]), str(latest["toFlame_cryptos"])]

    # Output folder: ...\260109\CAPS01\SH0130\
    out_dir = out_root / seq / shot
    out_dir.mkdir(parents=True, exist_ok=True)

    # Archive name = SHOT
    output_archive = str(out_dir / f"{shot}.7z")

    cmd = build_7z_split_command(
        seven_zip_exe=seven_zip_exe,
        output_archive=output_archive,
        source_dirs=sources,
        volume_size="4g",
        compression_level=0,  # store only (fastest for EXR)
    )

    print("Sequence/Shot:", seq, shot)
    print("Latest version directories found:")
    for k, v in latest.items():
        print(f"  {k}: {v}")

    print("\nOutput directory:")
    print(out_dir)

    print("\n7-Zip command:")
    print(" ".join(shlex.quote(x) for x in cmd))

    # Uncomment to run:
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
