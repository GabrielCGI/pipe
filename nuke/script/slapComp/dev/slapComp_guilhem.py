import subprocess
import sys
import os
import re

def find_highest_version(directory):
    highest_versions = {
        'CHARS': (None, None),  # (version_string, directory_path)
        'ENV': (None, None)
    }

    # Regex pattern to match folders like 'v0001', 'v0002', etc.
    pattern = re.compile(r'^v(\d+)$')

    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        # Normalize and uppercase current folder name to match against the targets
        current_folder = os.path.basename(os.path.normpath(root)).upper()
        # Check if we're in a subdirectory that matches 'CHARS' or 'ENV'
        if current_folder in ['CHARS', 'ENV']:
            for dir_name in dirs:
                match = pattern.match(dir_name)
                if match:
                    # Store the full version folder name (e.g., 'v0004')
                    version_folder_name = dir_name
                    # Extract the version number for comparison
                    version_number = int(match.group(1))
                    # Check if this version is greater than the current highest
                    if highest_versions[current_folder][0] is None or version_number > int(highest_versions[current_folder][0][1:]):
                        # Normalize the path to use forward slashes
                        folder_path = os.path.join(root, dir_name).replace('\\', '/')
                        highest_versions[current_folder] = (version_folder_name, folder_path)

    return highest_versions

def get_min_max_frames(path):
    global min_frame, max_frame  # Declare these as global so they can be accessed outside the function
    min_frame = float('inf')
    max_frame = -float('inf')

    # List all files in the directory
    try:
        files = [f for f in os.listdir(path) if f.endswith('.exr')]
    except FileNotFoundError:
        print("The specified directory does not exist.")
        min_frame, max_frame = None, None
        return

    if not files:
        print("No EXR files found in the directory.")
        min_frame, max_frame = None, None
        return

    # Debugging: Print all detected EXR files
    print(f"Found {len(files)} EXR files.")

    # Extract frame numbers and determine min/max
    for filename in files:
        parts = filename.split('.')
        if len(parts) > 2 and parts[-2].isdigit():  # Assuming the frame number is second last in the filename
            frame_number = int(parts[-2])
            min_frame = min(min_frame, frame_number)
            max_frame = max(max_frame, frame_number)
        else:
            print(f"Skipped file (no valid frame number found): {filename}")

    # Check if any valid frames were found
    if min_frame == float('inf') or max_frame == -float('inf'):
        print("No valid EXR files with frame numbers found.")
        min_frame, max_frame = None, None


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



# Set the starting directory path using forward slashes
rawpath = sys.argv[1]
path = rawpath.replace('\\', '/')


highest_versions = find_highest_version(path)

# Output the highest version folder paths and version strings for 'CHARS' and 'ENV'
chars_version, chars_folder = highest_versions['CHARS']
env_version, env_folder = highest_versions['ENV']

shot_number = path.split('/')[-1]




def run_nuke_command():

    

    # Define the command exactly as it would appear in a .bat file or command prompt 
    char_seq = chars_folder + '/beauty/mpa-' + shot_number + '_CHARS_' + chars_version + '_beauty.####.exr'
    env_seq =  env_folder + '/beauty/mpa-' + shot_number + '_ENV_' + env_version + '_beauty.####.exr'
    outpath_base = path + '/Renders/2dRender/SLAP_COMP/'
    
    new_version, outpath = get_next_version_path(outpath_base)
    outfile = outpath + '/mpa-'+ shot_number +'_SLAP_COMP_' + new_version + '.####.exr'
    get_min_max_frames(chars_folder+'/beauty')
    print(chars_folder)
    print(min_frame)

    outdir = os.path.dirname(outpath)
    if not os.path.exists(outdir):
        os.makedirs(outdir)  # This creates the directory including all necessary parent directories
        print(f"Created directory: {outdir}")
        

    # Set environment variables
    
    os.environ['START_FRAME'] = str(min_frame)
    os.environ['END_FRAME'] = str(max_frame)
    os.environ['CHARS_FILE'] = char_seq
    os.environ['ENV_FILE'] = env_seq
    os.environ['OUTPUT'] = outfile

    command = [
        r"C:\Program Files\Nuke12.1v5\Nuke12.1.exe",
        "-t",
        r"R:/pipeline/pipe/nuke/script/slapComp/slapComp_template_guilhem.py",
        chars_folder + '/mpa-' + shot_number + '_CHARS_' + chars_version + '_beauty.####.exr',
        env_folder + '/mpa-' + shot_number + '_ENV_' + env_version + '_beauty.####.exr',
        outfile.split('.')[0]+'.mov'
    ]

    try:
        # Run the commands
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

#"C:\Program Files\Nuke12.1v5\Nuke12.1.exe" -t "R:/pipeline/pipe/nuke/script/slapComp/slapComp_template_guilhem.py" "I:\myplace_2406\03_Production\Shots\mpa\100\Renders\3dRender\CHARS\v0002\beautympa-100_CHARS_v0002_beauty.####.exr" "I:/myplace_2406/03_Production/Shots/mpa/040/Renders/3dRender/ENV/v0002/beauty/mpa-040_ENV_v0002_beauty.####.exr" "D:/nuke/out_####.exr"
