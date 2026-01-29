import os
import sys
import subprocess

# Path to the Houdini autocrop utility
IAUTOCROP_EXE = r'C:\Program Files\Side Effects Software\Houdini 21.0.596\bin\iautocrop.exe'

def run_autocrop():
    # Expecting: script.py <directory> <start_frame> <end_frame>
    if len(sys.argv) < 4:
        print("Usage: python deadline_autocrop.py <directory> <start> <end>")
        sys.exit(1)

    target_dir = sys.argv[1]
    start_frame = int(sys.argv[2])
    end_frame = int(sys.argv[3])

    # 1. Identify the base name pattern from the directory
    # Based on your example: CAPS03-SH0310B_VEGET_v025_beauty.1001.exr
    # We find the .exr files to determine the prefix
    try:
        sample_file = [f for f in os.listdir(target_dir) if f.endswith(".exr")][0]
        # Split at the last dot before 'exr' to get the prefix (e.g., '...beauty')
        prefix = ".".join(sample_file.split(".")[:-2])
    except IndexError:
        print(f"No .exr files found in {target_dir}")
        sys.exit(1)

    # 2. Loop through the specific range provided by Deadline
    for frame in range(start_frame, end_frame + 1):
        # Format frame to 4-digit padding (1001)
        filename = f"{prefix}.{frame:04d}.exr"
        file_path = os.path.join(target_dir, filename)

        if os.path.exists(file_path):
            print(f"Cropping frame {frame}: {file_path}")
            command = [IAUTOCROP_EXE, "-r", file_path]
            subprocess.run(command, check=True)
        else:
            print(f"Skipping: {filename} (File not found)")

if __name__ == "__main__":
    run_autocrop()