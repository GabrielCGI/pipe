import os
import glob
import subprocess
import re

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

def check_last_two_lines(filepath, target_string):
    with open(filepath, 'r') as file:
        lines = file.readlines()

        last_two_lines = lines[-2:]
        third_last_line = lines[-3]
        print (last_two_lines)
        print(third_last_line)
        if all(target_string in line for line in last_two_lines):
            if not "rays/pixel" in third_last_line:
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
        new_check_string = "Skipping thermal shutdown check because it is not required at this time"
        check_string = check_string_in_file(latest_file, target_string)
        check_last_two = check_last_two_lines(latest_file, new_check_string)

        if check_string or check_last_two:
            print("##########################################")
            print("##########################################")
            print("##########################################")
            print ("check_string_in_file (found if true):"+ str(check_string))
            print("check_last_two_lines: (found if true) "+ str(check_last_two))
            print("##########################################")
            print("##########################################")
            print("##########################################")
            kill_process('mayabatch.exe')
        else:

            print(f"No Sandbox or Skipping termal check met in the file.")

    else:
        print("No matching files found.")

if __name__ == "__main__":
    main()
