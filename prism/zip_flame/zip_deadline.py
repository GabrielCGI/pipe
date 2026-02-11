import sys
import shlex
import subprocess
from pathlib import Path
from typing import Tuple, List

SEVEN_ZIP_EXE = r"C:\Program Files\7-Zip\7z.exe"
FLAME_ROOT = Path(r"I:\VCA_Perlee_2510\08_Flame")

# EXR sequences: store only is usually best + fastest
COMPRESSION_LEVEL = 0   # 0=store, 1=fast
VOLUME_SIZE = "4g"      # e.g. "2g", "4g", "700m"


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
        f"-mx={COMPRESSION_LEVEL}",
        f"-v{VOLUME_SIZE}",
        output_archive,
        *sources,
    ]


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage:")
        print('  python zip_to_flame.py "<input_2dRender_dir>" "<date_folder>"')
        return 1

    input_dir = Path(sys.argv[1])
    date_folder = sys.argv[2].strip()

    if not input_dir.exists():
        raise RuntimeError(f"Input directory does not exist: {input_dir}")

    print("Input dir:", input_dir)
    print("Date folder:", date_folder)

    seq, shot = extract_seq_shot_from_path(input_dir)

    # Zip entire folders (no version logic)
    beauty_dir = input_dir / "toFlame_beauty"
    cryptos_dir = input_dir / "toFlame_cryptos"

    missing = [str(p) for p in (beauty_dir, cryptos_dir) if not p.exists()]
    if missing:
        raise RuntimeError("Missing expected folder(s):\n  " + "\n  ".join(missing))

    sources = [str(beauty_dir), str(cryptos_dir)]

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
