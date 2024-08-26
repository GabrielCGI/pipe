import subprocess

def run_nuke_command():
    # Define the command exactly as it would appear in a .bat file or command prompt
    command = [
        r"C:\Program Files\Nuke12.1v5\Nuke12.1.exe",
        "-t",
        r"R:/pipeline/pipe/nuke/script/slapComp/slapComp_template.py",
        r"I:/myplace_2406/03_Production/Shots/mpa/040/Renders/3dRender/CHARS/v0002/beauty/mpa-040_CHARS_v0002_beauty.####.exr",
        r"D:/nuke/out_####.exr"
    ]

    try:
        # Run the command
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

#"C:\Program Files\Nuke12.1v5\Nuke12.1.exe" -t "R:/pipeline/pipe/nuke/script/slapComp/slapComp_template.py" "I:/myplace_2406/03_Production/Shots/mpa/040/Renders/3dRender/CHARS/v0002/beauty/mpa-040_CHARS_v0002_beauty.####.exr" "D:/nuke/out_####.exr"
