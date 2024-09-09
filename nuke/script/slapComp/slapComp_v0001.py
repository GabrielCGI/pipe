import subprocess
import sys
import os
import re

def find_versions(directory):
    versions = {}
    folder_count = 0  # Initialize the counter

    pattern = re.compile(r'^v(\d+)$')

    for item in os.listdir(directory):
        sub_dir = os.path.join(directory, item)
        if os.path.isdir(sub_dir):
            folder_count +=1
            current_folder = os.path.basename(os.path.normpath(sub_dir)).upper()
            versions[current_folder] = []
            iteration = 0
            for dir_name in os.listdir(sub_dir):              
                dir_path = os.path.join(sub_dir, dir_name)
                if os.path.isdir(dir_path):
                    match = pattern.match(dir_name)
                    if match:
                        version_number = int(match.group(1))
                        folder_path = dir_path.replace('\\', '/')
                        versions[current_folder].append((version_number, folder_path))
                        

    for folder in versions:
        versions[folder].sort(reverse=True)  # Sort by version number descending

    return versions, folder_count  # Return both the versions dictionary and the folder count

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

    next_version_number = max_version + 1
    next_version = f"v{next_version_number:04d}"
    next_version_path = os.path.join(base_dir, next_version)

    # Check if the next version path already exists and increment if necessary
    while os.path.exists(next_version_path):
        next_version_number += 1
        next_version = f"v{next_version_number:04d}"
        next_version_path = os.path.join(base_dir, next_version)

    os.makedirs(next_version_path)
    print('')
    print(f"Output directory : {next_version_path}")
    return next_version, next_version_path



def choose_version(versions, folder_name):
    if not versions.get(folder_name):
        print(f"No versions available for {folder_name}.")
        return None, None

    print(f"Available versions for {folder_name}:")
    for index, (version_number, path) in enumerate(versions[folder_name]):
        print(f"{index}: Version {version_number:04d} at {path}")

    while True:
        try:
            choice = int(input(f"Choose a version index for {folder_name}: "))
            if 0 <= choice < len(versions[folder_name]):
                print('')
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

    # Add detected frame ranges
    index = 0
    for folder_name, min_frame, max_frame in folder_ranges:
        if min_frame is not None and max_frame is not None:
            print(f"[{index}] {folder_name} frame range is {min_frame}-{max_frame}")
            options.append((min_frame, max_frame))
            index += 1
        else:
            print(f"{folder_name} frame range: No frame range detected")

    # Add custom frame range option
    print(f"[{index}] Enter custom frame range")
    options.append(None)  # Placeholder for custom input

    while True:
        try:
            choice = int(input(f"Choose an option (0-{len(options) - 1}): "))
            if choice == len(options) - 1:
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
            elif 0 <= choice < len(options) - 1:
                # Valid detected range
                return options[choice]
            else:
                print(f"Invalid choice. Please choose a valid option between 0 and {len(options) - 1}.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def run_nuke_command():
    print('')
    print('Welcome to SlapComper !')
    print('')
    rawpath = sys.argv[1]
    path = rawpath.replace('\\', '/')
    shot_parent_folder = path.split('/')[-2]
    versions, num_folders = find_versions(path + '/Renders/3dRender/')

    # Automatically process all detected folders and versions
    chosen_versions = {}
    for folder_name in versions:
        chosen_versions[folder_name] = choose_version(versions, folder_name)


    shot_number = path.split('/')[-1]

    # Detect frame ranges
    folder_ranges = []
    for folder_name, (version, folder) in chosen_versions.items():
        min_frame, max_frame = get_min_max_frames(folder + '/beauty') if folder else (None, None)
        folder_ranges.append((folder_name, min_frame, max_frame))

    # Allow user to choose frame range
    min_frame, max_frame = choose_frame_range(folder_ranges)

    sequences = {}
    sequence_order = []
    print("\nChoose the order of sequences for merging:")
    for index, folder_name in enumerate(chosen_versions.keys()):
        print(f"[{index}] {folder_name}")
    while len(sequence_order) < len(chosen_versions):
        try:
            choice = int(input(f"Select the next sequence to merge (0-{len(chosen_versions)-1}): "))
            if 0 <= choice < len(chosen_versions) and choice not in sequence_order:
                sequence_order.append(choice)
            else:
                print("Invalid choice or sequence already chosen. Please select another sequence.")
        except ValueError:
            print("Please enter a valid integer.")

    for index in sequence_order:
        folder_name = list(chosen_versions.keys())[index]
        version, folder = chosen_versions[folder_name]
        if folder:
            sequences[folder_name] = f"{folder}/beauty/{shot_parent_folder}-{shot_number}_{folder_name}_{version}_beauty.####.exr"

    outpath_base = path + '/Renders/2dRender/SLAP_COMP/'
    new_version, outpath = get_next_version_path(outpath_base)

    
    print('Output file format : ')
    print()
    print('[0] exr')
    print('[1] mov')
    outformat = int(input('Choose output format : '))

    if outformat == 0 :
        outfile = outpath + '/' + shot_parent_folder + '-' + shot_number + '_SLAP_COMP_' + new_version + '.####.exr'
        outformat = 'exr'
    if outformat == 1 :
        outfile = outpath + '/' + shot_parent_folder + '-' + shot_number + '_SLAP_COMP_' + new_version + '.mov'
        outformat = 'mov'

    print('')
    print('Launching Nuke...')
    print('')

    outdir = os.path.dirname(outpath)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
        print(f"Created directory: {outdir}")

    num_it = 'Iterations_'+str(num_folders)

    command = [
        r"C:\Program Files\Nuke12.1v5\Nuke12.1.exe",
        "-t",
        r"R:/pipeline/pipe/nuke/script/slapComp/slapComp_template_v0001.py",
        num_it,
        str(min_frame),
        str(max_frame),
        outfile,
        outformat,
    ]

    for index in sequence_order:
        folder_name = list(chosen_versions.keys())[index]
        seq = sequences[folder_name]
        command.append('filepath='+seq)

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