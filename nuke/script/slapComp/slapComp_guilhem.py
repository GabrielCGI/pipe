import subprocess
import sys

def run_nuke_command():
    # Define the command exactly as it would appear in a .bat file or command prompt
    sourceA = sys.argv[1]
    sourceB = sys.argv[2]
    outpath = sys.argv[3]
    command = [
        r"C:\Program Files\Nuke12.1v5\Nuke12.1.exe",
        "-t",
        r"R:/pipeline/pipe/nuke/script/slapComp/slapComp_template.py",
        source_A,
        source_B,
        outpath + r"\out_####.exr"
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

#"C:\Program Files\Nuke12.1v5\Nuke12.1.exe" -t "R:/pipeline/pipe/nuke/script/slapComp/slapComp_template_guilhem.py" "I:\myplace_2406\03_Production\Shots\mpa\100\Renders\3dRender\CHARS\v0002\beautympa-100_CHARS_v0002_beauty.####.exr" "I:/myplace_2406/03_Production/Shots/mpa/040/Renders/3dRender/ENV/v0002/beauty/mpa-040_ENV_v0002_beauty.####.exr" "D:/nuke/out_####.exr"
