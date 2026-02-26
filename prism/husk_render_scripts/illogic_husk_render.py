
import os
import sys
import subprocess
import json

# --------------------------------------------------------------------------
# ILLOGIC CUSTOM PART
# --------------------------------------------------------------------------
import socket
import shutil

LOCAL_DRIVE_I       = "I:/"
LOCAL_DRIVE_R       = "R:/"

UNC_RANCH_CACHE_I   = "//RANCH-SERVER/ranch_cache/I/"
UNC_RANCH_CACHE_R   = "//RANCH-SERVER/ranch_cache/R/"  

RANCH_OUT_EXR_DIR     = "C:/RANCH_OUT_EXR/"
LOCAL_EXR_COPY_DIR    = "I:/" # /!\/!\/!\/!\/!\/!\ CHANGE THIS TO SOMETHING LIKE "C:/test/" if you need to modify this code.
IS_EXR_COPY_ONLY_TEST_MODE = False
DELETE_LOCAL_EXR_AFTER_COPY = True


def copy_if_missing(src, dst):
    """Copy 'src' to 'dst' only if 'dst' doesn't exist."""
    if os.path.exists(dst):
        print(f"'{dst}' already exists. Skipping copy.")
        return
    print(f"Copying '{src}' => '{dst}'")
    try:
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        else:
            shutil.copytree(src, dst)
    except Exception as e:
        print(f"Error copying '{src}': {e}")

     
def replace_prefix(path: str, replacements: dict):
    """
    Replace the first matching prefix from 'replacements' dict in 'path'.
    Returns 'path' unchanged if no prefixes match.
    """
    for old_prefix, new_prefix in replacements.items():
        if path.startswith(old_prefix):
            return path.replace(old_prefix, new_prefix, 1)
    return path


def remap_ranch_usd_and_output(usd_file_path: str, img_output: str, env_copy: dict):
    """
    Overwrite environment variables for RANCH usage and remap local I:/, R:/ 
    to UNC ranch cache paths. Also remaps I:/ in 'img_output' to 'C:/RANCH_OUT_EXR/'.
    """
    PXR_AR_DEFAULT_SEARCH_PATH_RANCH = f"{UNC_RANCH_CACHE_I};{UNC_RANCH_CACHE_R};I:/;R:/"
    env_copy["PXR_AR_DEFAULT_SEARCH_PATH"] = PXR_AR_DEFAULT_SEARCH_PATH_RANCH
    
    print(f'PXR AR DEFAULT SEARCH PATH: {env_copy["PXR_AR_DEFAULT_SEARCH_PATH"]}')
    print("Ranch machine detected - remapping USD/file paths.")

    # Convert to UNC ranch cache if missing
    usd_mapped = replace_prefix(usd_file_path, {
        LOCAL_DRIVE_I: UNC_RANCH_CACHE_I, 
        LOCAL_DRIVE_R: UNC_RANCH_CACHE_R
    })

    print(f"Remap: {usd_file_path} => {usd_mapped}")

    # Copy to UNC ranch location if missing
    if not os.path.exists(usd_mapped) and os.path.exists(usd_file_path):
        os.makedirs(os.path.dirname(usd_mapped), exist_ok=True)
        copy_if_missing(usd_file_path, usd_mapped)
    else:
        print(f"'{usd_mapped}' already exists or '{usd_file_path}' not found.")

    # Remap output path from I:/ to C:/RANCH_OUT_EXR/
    updated_output = replace_prefix(img_output, {
        LOCAL_DRIVE_I: RANCH_OUT_EXR_DIR
    })
    print(f"Output path: {img_output} => {updated_output}")

    # Ensure the output directory exists
    out_dir = os.path.dirname(updated_output)
    existed = os.path.exists(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    print(f"Output dir '{out_dir}' {'existed' if existed else 'created'}.")

    return usd_mapped, updated_output, env_copy


def copy_exr_from_ranch_to_network(
    ranch_shot_exr_dir,
    local_exr_copy_dir=LOCAL_EXR_COPY_DIR,
    ranch_out_exr_dir=RANCH_OUT_EXR_DIR,
    delete_local_exr_after_copy = False
):
    """
    Copy .exr files from 'ranch_shot_exr_dir' to 'local_exr_copy_dir',
    removing originals on success, unless 'is_test_mode' is True.
    """

    print("Script started.")
    print(f"Source directory: {ranch_shot_exr_dir}")

    if not os.path.isdir(ranch_shot_exr_dir):
        raise (f"Source directory not found: {ranch_shot_exr_dir}")


    for root, _, files in os.walk(ranch_shot_exr_dir):
        for file_name in files:
            if not file_name.lower().endswith(".exr"):
                continue
            src_file = os.path.join(root, file_name)
            # Build the new path (replace the ranch prefix with local_exr_copy_dir)
            dst_file = src_file.replace(ranch_out_exr_dir, local_exr_copy_dir, 1)
            try:
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                shutil.copy2(src_file, dst_file)
                print(f"Copied: {src_file} -> {dst_file}")
                if delete_local_exr_after_copy:
                    try:
                        os.remove(src_file)
                        print(f"Deleted: {src_file}")
                    except PermissionError:
                        raise (f"Perm denied: {src_file}")
                    except Exception as e:
                        raise (f"Error deleting '{src_file}': {e}")
                else:
                    print(f"DELETE_LOCAL_EXR_AFTER_COPY is FALSE. Skip delete: {src_file}")
            except PermissionError:
                raise (f"Perm denied copying '{src_file}' -> '{dst_file}'.")
            except FileNotFoundError:
                raise (f"File/path missing '{src_file}' -> '{dst_file}'.")
            except OSError as e:
                raise (f"OS error copying '{src_file}' -> '{dst_file}': {e}")
            except Exception as e:
                raise (f"Unexpected error copying '{src_file}' -> '{dst_file}': {e}")

    print("Script finished.")


# --------------------------------------------------------------------------
# MAIN SCRIPT
# --------------------------------------------------------------------------
settingsFile = sys.argv[3]
endFrame = int(sys.argv[2])
startFrame = int(sys.argv[1])

executable = os.getenv("HUSK_PATH")
if not executable or not os.path.exists(executable):
    executable = os.getenv("PRISM_DEADLINE_HUSK_PATH")
    if not executable or not os.path.exists(executable):
        raise Exception(
            "The Husk render executable is not defined or doesn't exist.\n"
            "Use \"HUSK_PATH\" or \"PRISM_DEADLINE_HUSK_PATH\" "
            "environment variable to specify a valid path."
        )

with open(os.path.dirname(__file__) + "/" + settingsFile, "r") as f:
    settings = json.load(f)

renderer = settings["renderer"]
renderSettings = settings["rendersettings"]
imgOutput: str = settings["outputpath"]
usdFilePath: str = settings["usdfile"]
frameCount = str(endFrame-startFrame+1)
useTiles = settings.get("useTiles", False)
tilesX = settings.get("tilesX", 1)
tilesY = settings.get("tilesY", 1)
# ILLOGIC_CUSTOM << - Parse tilesX and tilesY even when rendering a sequence
enableTiles = bool(int(settings.get("enable_tile", "0")))
tiles_1 = settings.get("tiles_1", "1")
tiles_2 = settings.get("tiles_2", "1")
enableAutoCrop = settings.get("enable_autocrop", True)
autocrop_aovs = settings.get("autocrop_aovs", "C,A,holdout_shadows")
# END >>
if useTiles:
    tileFrame = int(settings.get("startFrame", 1))
    tileIdx = startFrame - tileFrame # Potential mistake from Prism | tileFrame - startFrame
    startFrame = endFrame = tileFrame
    frameCount = "1"
    base, ext = os.path.splitext(imgOutput)
    if "$F4" in imgOutput:
        base = base.replace("$F4", "%04d" % startFrame).strip(".")
        ext = base[-5:] + ext
        base = base[:-5]

    xtile = tileIdx % tilesX
    ytile = int(tileIdx/tilesY)
    tileSuffix = "_tile_%sx%s_%sx%s_" % (xtile+1, ytile+1, tilesX, tilesY)

def readStdout(proc):
    while True:
        line = proc.stdout.readline()
        line = line.decode("utf-8", errors="ignore")
        if "ALF_PROGRESS" in line:
            print("Progress: %s" % line.replace("ALF_PROGRESS ", ""))

        if line == '' and proc.poll() is not None:
            break

        print(line)


# imgOutput = "\"%s\"" % imgOutput
usdFilePath = usdFilePath.replace("####", "$F4")
# ILLOGIC_CUSTOM << - Setup environment
os.environ.pop("HOUDINI_PACKAGE_DIR", None)
os.environ["PXR_AR_DEFAULT_SEARCH_PATH"] = f"{LOCAL_DRIVE_I};{LOCAL_DRIVE_R}"
env_copy = dict(os.environ)
computer_name = socket.gethostname()
if computer_name.startswith("RANCH") and "nocache" not in usdFilePath:
    usdFilePath, imgOutput, env_copy = remap_ranch_usd_and_output(usdFilePath, imgOutput, env_copy)
# END >>
args = [
    executable,
    usdFilePath,
    "--output",
    imgOutput,
    "--frame",
    str(startFrame),
    "--frame-count",
    frameCount,
    "--renderer",
    renderer,
    "--verbose",
    "aC6",
    "--settings",
    renderSettings,
#   "--windows-console",
#    "wait",
]

if settings.get("legacyExrMode"):
    args += ["--exrmode", settings.get("legacyExrMode")]

if settings.get("camera"):
    args += ["--camera", settings.get("camera")]

if settings.get("width") and settings.get("height"):
    width = settings.get("width")
    height = settings.get("height")
    args += ["--res", str(width), str(height)]

if useTiles:
    args += ["--tile-count", str(tilesX), str(tilesY)]
    args += ["--tile-index", str(tileIdx)]
    args += ["--tile-suffix", tileSuffix]

# ILLOGIC_CUSTOM << - Enable autotile on sequence
elif enableTiles:
    args += ["--autotile"]
    args += ["--tile-count", tiles_1, tiles_2]
# END >>
# ILLOGIC_CUSTOM << - Enable autocrop
if enableAutoCrop:
    args += "--autocrop", autocrop_aovs
# END >>

print("command args: %s" % (args))
# ILLOGIC_CUSTOM - Add custom env to subprocess
p = subprocess.Popen(args, stdout=subprocess.PIPE, env=env_copy)
readStdout(p)

lastFrame = imgOutput.replace("$F4", "%04d" % (endFrame))
if useTiles:
    base, ext = os.path.splitext(lastFrame)
    lastFrame = base + tileSuffix + ext

if p.returncode:
    raise RuntimeError("renderer exited with code %s" % p.returncode)
elif not os.path.exists(lastFrame):
    raise RuntimeError("expected output doesn't exist %s" % (lastFrame))
else:
    # ILLOGIC_CUSTOM << On RANCH computers, copy EXRs back to network
    if computer_name.startswith("RANCH"):
        print("Start copying EXRs back to network...")
        shot_dir = os.path.dirname(imgOutput)
        copy_exr_from_ranch_to_network(
            ranch_shot_exr_dir=shot_dir,
            ranch_out_exr_dir=RANCH_OUT_EXR_DIR,
            delete_local_exr_after_copy=DELETE_LOCAL_EXR_AFTER_COPY # Set False to do real copy & delete
        )
    else:
        print("Skipping EXR copy-back")
    # END >>
    print("task completed successfully")
