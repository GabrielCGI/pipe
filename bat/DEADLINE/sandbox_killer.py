import os
import glob
import subprocess

def get_computer_name():
    return os.environ['COMPUTERNAME']

def find_latest_file(log_directory, pattern):
    os.chdir(log_directory)
    files = glob.glob(pattern)

    latest_file = None
    latest_mtime = None

    for file in files:
        mtime = os.path.getmtime(file)
        if latest_mtime is None or mtime > latest_mtime:
            latest_mtime = mtime
            latest_file = file

    return latest_file

def check_string_in_file(filepath, target_string):
    with open(filepath, 'r') as file:
        lines = file.readlines()
        last_lines = lines[-10:]

        for line in last_lines:
            if target_string in line:
                return True
    return False
def kill_process(process_name):
    try:
        subprocess.run(['taskkill', '/IM', process_name, '/F'], check=True, text=True)
        print(f"Killed '{process_name}' process.")
    except subprocess.CalledProcessError:
        print(f"'{process_name}' process not found or could not be killed.")

def main():
    computer_name = get_computer_name()

    log_directory = "C:\\ProgramData\\Thinkbox\\Deadline10\\logs"
    pattern = f"deadlineslave-{computer_name}*"

    latest_file = find_latest_file(log_directory, pattern)

    if latest_file:
        print("--------------------------------")
        print(f"The last modified file is: {latest_file}")
        target_string = "SandboxedPlugin still waiting for SandboxThread to exit"
        if check_string_in_file(latest_file, target_string):
            print(f"The string '{target_string}' was found in the file")
            kill_process('mayabatch.exe')
        else:
            print(f"The string '{target_string}' was not found in the file.")
    else:
        print("No matching files found.")

if __name__ == "__main__":
    main()
