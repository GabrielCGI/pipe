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

# Set the starting directory path using forward slashes
path = "I:/myplace_2406/03_Production/Shots/mpa/100"
highest_versions = find_highest_version(path)

# Output the highest version folder paths and version strings for 'CHARS' and 'ENV'
chars_version, chars_folder = highest_versions['CHARS']
env_version, env_folder = highest_versions['ENV']

if chars_folder:
    print(f"The highest version folder in 'CHARS' is: {chars_folder} (Version: {chars_version})")
else:
    print("No version folder found in 'CHARS' matching the pattern 'vXXXX'.")

if env_folder:
    print(f"The highest version folder in 'ENV' is: {env_folder} (Version: {env_version})")
else:
    print("No version folder found in 'ENV' matching the pattern 'vXXXX'.")

print(chars_version)
print(chars_folder)
shot_number = path.split('/')[-1]
char_seq = chars_folder + '/mpa-' + shot_number + '_CHARS_' + chars_version + '_beauty.####.exr'
print(shot_number)
print(char_seq)
