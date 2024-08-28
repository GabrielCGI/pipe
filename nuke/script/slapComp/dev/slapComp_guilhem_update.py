import subprocess
import sys
import os
import re

def find_versions(directory):
    versions = {
        'ALL': [],
        'VOL': [],
        'CHARS': [],
        'ENV': []
    }

    pattern = re.compile(r'^v(\d+)$')

    for root, dirs, files in os.walk(directory):
        current_folder = os.path.basename(os.path.normpath(root)).upper()
        if current_folder in ['ALL','VOL','CHARS', 'ENV']:
            for dir_name in dirs:
                match = pattern.match(dir_name)
                if match:
                    version_number = int(match.group(1))
                    folder_path = os.path.join(root, dir_name).replace('\\', '/')
                    versions[current_folder].append((version_number, folder_path))

    for folder in versions:
        versions[folder].sort(reverse=True)  # Sort by version number descending

    return versions

def get_min_max_frames(path):
    min_frame = float('inf')
    max_frame = -float('inf')

    try:
        files = [f for f in os.listdir(path) if f.endswith('.exr')]
    except FileNotFoundError:
        print(f"The specified directory {path} does not exist.")
        return None, None

    if not files:
        print(f"No EXR files found in the directory {path}.")
        return None, None

    print(f"Found {len(files)} EXR files in {path}.")

    for filename in files:
        parts = filename.split('.')
        if len(parts) > 2 and parts[-2].isdigit():
            frame_number = int(parts[-2])
            min_frame = min(min_frame, frame_number)
            max_frame = max(max_frame, frame_number)
        else:
            print(f"Skipped file (no valid frame number found): {filename}")

    if min_frame == float('inf') or max_frame == -float('inf'):
        print(f"No valid EXR files with frame numbers found in {path}.")
        return None, None

    return min_frame, max_frame

def get_next_version_path(base_dir):
    pattern = re.compile(r'^v(\d+)$')
    max_version = 0
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        print(f"Created base directory: {base_dir}")
    for item in os.listdir(base_dir):
        if os.path.isdir(os.path.join(base_dir, item)):
            match = pattern.match(item)
            if match:
                version_number = int(match.group(1))
                max_version = max(max_version, version_number)
    next_version = f"v{max_version + 1:04d}"
    next_version_path = os.path.join(base_dir, next_version)
    os.makedirs(next_version_path)
    print(f"Created next version directory: {next_version_path}")
    return next_version, next_version_path


def choose_version(versions, folder_name):
    if not versions[folder_name]:
        print(f"No versions available for {folder_name}.")
        return None, None

    print(f"Available versions for {folder_name}:")
    for index, (version_number, path) in enumerate(versions[folder_name]):
        print(f"{index}: Version {version_number:04d} at {path}")

    while True:
        try:
            choice = int(input(f"Choose a version index for {folder_name}: "))
            if 0 <= choice < len(versions[folder_name]):
                break
            else:
                print(f"Invalid choice. Please choose a number between 0 and {len(versions[folder_name]) - 1}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    chosen_version = versions[folder_name][choice]
    return f"v{chosen_version[0]:04d}", chosen_version[1]

def choose_frame_range(folder_ranges):
    print("\nFrame range options:")

    options = []

    # Add custom frame range option
    print("[0] Enter custom frame range")
    options.append(None)  # Placeholder for custom input

    # Add detected frame ranges
    index = 1
    for folder_name, min_frame, max_frame in folder_ranges:
        if min_frame is not None and max_frame is not None:
            print(f"[{index}] {folder_name} frame range is {min_frame}-{max_frame}")
            options.append((min_frame, max_frame))
            index += 1
        else:
            print(f"{folder_name} frame range: No frame range detected")

    while True:
        try:
            choice = int(input(f"Choose an option (0-{len(options) - 1}): "))
            if choice == 0:
                # Custom range
                custom_range = input("Enter custom frame range (minframe-maxframe): ")
                try:
                    custom_min_frame, custom_max_frame = map(int, custom_range.split('-'))
                    if custom_min_frame <= custom_max_frame:
                        return custom_min_frame, custom_max_frame
                    else:
                        print("Invalid range. Minimum frame should be less than or equal to maximum frame.")
                except ValueError:
                    print("Invalid input. Please enter the range in the form minframe-maxframe.")
            elif 1 <= choice < len(options):
                # Valid detected range
                return options[choice]
            else:
                print(f"Invalid choice. Please choose a valid option between 0 and {len(options) - 1}.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def run_nuke_command():

    rawpath = sys.argv[1]
    path = rawpath.replace('\\', '/')
    shot_parent_folder = path.split('/')[-2]
    versions = find_versions(path)

    all_version, all_folder = choose_version(versions, 'ALL')
    vol_version, vol_folder = choose_version(versions, 'VOL')
    chars_version, chars_folder = choose_version(versions, 'CHARS')
    env_version, env_folder = choose_version(versions, 'ENV')
    

    shot_number = path.split('/')[-1]

    # Detect frame ranges
    all_min_frame, all_max_frame = get_min_max_frames(all_folder + '/beauty') if all_folder else (None, None)
    vol_min_frame, vol_max_frame = get_min_max_frames(vol_folder + '/beauty') if vol_folder else (None, None)
    chars_min_frame, chars_max_frame = get_min_max_frames(chars_folder + '/beauty') if chars_folder else (None, None)
    env_min_frame, env_max_frame = get_min_max_frames(env_folder + '/beauty') if env_folder else (None, None)

    # Prepare folder ranges for selection
    folder_ranges = [
        ('ALL', all_min_frame, all_max_frame),
        ('VOL', vol_min_frame, vol_max_frame),
        ('CHARS', chars_min_frame, chars_max_frame),
        ('ENV', env_min_frame, env_max_frame),   
    ]

    # Allow user to choose frame range
    min_frame, max_frame = choose_frame_range(folder_ranges)

    char_seq = chars_folder + '/beauty/'+ shot_parent_folder + '-' + shot_number + '_CHARS_' + chars_version + '_beauty.####.exr' if chars_folder else None
    env_seq = env_folder + '/beauty/'+ shot_parent_folder + '-' + shot_number + '_ENV_' + env_version + '_beauty.####.exr' if env_folder else None
    all_seq = all_folder + '/beauty/'+ shot_parent_folder + '-' + '_ALL_' + all_version + '_beauty.####.exr' if all_folder else None
    vol_seq = vol_folder + '/beauty/'+ shot_parent_folder + '-' + '_ALL_' + vol_version + '_beauty.####.exr' if vol_folder else None


    outpath_base = path + '/Renders/2dRender/SLAP_COMP/'

    new_version, outpath = get_next_version_path(outpath_base)
    outfile = outpath + '/' + shot_parent_folder + '-' + shot_number + '_SLAP_COMP_' + new_version + '.####.exr'

    outdir = os.path.dirname(outpath)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
        print(f"Created directory: {outdir}")

    os.environ['START_FRAME'] = str(min_frame)
    os.environ['END_FRAME'] = str(max_frame)
    os.environ['CHARS_FILE'] = str(char_seq)
    os.environ['ENV_FILE'] = str(env_seq)
    os.environ['ALL'] = str(all_seq)
    os.environ['VOL']= str(vol_seq)
    os.environ['OUTPUT'] = outfile

    command = [
        r"C:\Program Files\Nuke12.1v5\Nuke12.1.exe",
        "-t",
        r"R:/pipeline/pipe/nuke/script/slapComp/slapComp_template_guilhem.py",
        outfile.split('.')[0] + '.mov',
    ]

    try:
        subprocess.run(command, check=True)
        print("Nuke process ran successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the Nuke process: {e}")
    except FileNotFoundError:
        print("Nuke executable not found at the specified path.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    run_nuke_command()