import os
import sys
import subprocess
import json

# --------------------------------------------------------------------------
# ILLOGIC CUSTOM PART
# --------------------------------------------------------------------------
import shutil
import logging
import datetime

LOCAL_DRIVE_I       = "I:/"
LOCAL_DRIVE_R       = "R:/"

LOCAL_RANCH_CACHE_I = "I:/ranch_cache2/I/"

UNC_RANCH_CACHE_I   = "\\\\RANCH-SERVER\\ranch_cache2\\I\\"
UNC_RANCH_CACHE_R   = "\\\\RANCH-SERVER\\ranch_cache2\\r\\"   

RANCH_OUT_EXR_DIR     = "C:/RANCH_OUT_EXR/"
RANCH_OUT_EXR_LOG_DIR = "C:/RANCH_OUT_EXR_log/"
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
        
def copy_cop_textures(src_path, dst_path):
    """
    Copy any '.textures' directories next to 'src_path' into:
      1) The local 'dst_path'
      2) The local ranch cache location.
    """
    src_parent = os.path.dirname(os.path.abspath(src_path))
    dst_parent = os.path.dirname(os.path.abspath(dst_path))

    # Something like I:/ranch_cache2/I/<subfolders...>
    drive, tail = os.path.splitdrive(src_parent)
    tail = tail.lstrip("\\/")
    ranchcache_dir = os.path.join(LOCAL_RANCH_CACHE_I, tail)

    for item in os.listdir(src_parent):
        item_path = os.path.join(src_parent, item)
        if os.path.isdir(item_path) and item.endswith('.textures'):
            copy_if_missing(item_path, os.path.join(dst_parent, item))
            copy_if_missing(item_path, os.path.join(ranchcache_dir, item))
        
def replace_prefix(path, replacements):
    """
    Replace the first matching prefix from 'replacements' dict in 'path'.
    Returns 'path' unchanged if no prefixes match.
    """
    for old_prefix, new_prefix in replacements.items():
        if path.startswith(old_prefix):
            return path.replace(old_prefix, new_prefix, 1)
    return path

def remap_ranch_usd_and_output(usd_file_path, img_output, env_copy):
    """
    Overwrite environment variables for RANCH usage and remap local I:/, R:/ 
    to UNC ranch cache paths. Also remaps I:/ in 'img_output' to 'C:/RANCH_OUT_EXR/'.
    """
    PXR_AR_DEFAULT_SEARCH_PATH_RANCH = f"{UNC_RANCH_CACHE_I};{UNC_RANCH_CACHE_R};I:/;R:/"
    env_copy["PXR_AR_DEFAULT_SEARCH_PATH"] = PXR_AR_DEFAULT_SEARCH_PATH_RANCH
    print(f'PXR AR DEFAULT SEARCH PATH: {env_copy["PXR_AR_DEFAULT_SEARCH_PATH"]}')
    print("Ranch machine detected - remapping USD/file paths.")

    # Convert to UNC ranch cache if missing
    usd_mapped    = replace_prefix(usd_file_path, {
        LOCAL_DRIVE_I: UNC_RANCH_CACHE_I, 
        LOCAL_DRIVE_R: UNC_RANCH_CACHE_R
    })
    usd_local_ranch = replace_prefix(usd_file_path, {
        LOCAL_DRIVE_I: LOCAL_RANCH_CACHE_I
    })

    print(f"Remap: {usd_file_path} => {usd_mapped}")
    print(f"Remap: {usd_file_path} => {usd_local_ranch}")

    # Copy to UNC ranch location if missing
    if not os.path.exists(usd_mapped) and os.path.exists(usd_file_path):
        os.makedirs(os.path.dirname(usd_mapped), exist_ok=True)
        copy_if_missing(usd_file_path, usd_mapped)
    else:
        print(f"'{usd_mapped}' already exists or '{usd_file_path}' not found.")

    # Copy to local ranch cache if missing
    if not os.path.exists(usd_local_ranch) and os.path.exists(usd_file_path):
        os.makedirs(os.path.dirname(usd_local_ranch), exist_ok=True)
        copy_if_missing(usd_file_path, usd_local_ranch)
    else:
        print(f"'{usd_local_ranch}' already exists or '{usd_file_path}' not found.")

    # Copy .textures directories if present
    copy_cop_textures(usd_file_path, usd_mapped)

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
    ranch_shot_exr_dir="C:/RANCH_OUT_EXR/productionA/shotB",
    local_exr_copy_dir=LOCAL_EXR_COPY_DIR,
    ranch_out_exr_dir=RANCH_OUT_EXR_DIR,
    is_test_mode=True,
    delete_local_exr_after_copy = False
):
    """
    Copy .exr files from 'ranch_shot_exr_dir' to 'local_exr_copy_dir',
    removing originals on success, unless 'is_test_mode' is True.
    """

    # Helper functions to log AND print
    def log_info(msg):
        logging.info(msg)
        print(msg)

    def log_error(msg):
        logging.error(msg)
        print(msg)

    # Prepare logging
    os.makedirs(RANCH_OUT_EXR_LOG_DIR, exist_ok=True)
    log_filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_copy_exr.log")
    log_path = os.path.join(RANCH_OUT_EXR_LOG_DIR, log_filename)

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    log_info("Script started.")
    log_info(f"Source directory: {ranch_shot_exr_dir}")

    if not os.path.isdir(ranch_shot_exr_dir):
        log_error(f"Source directory not found: {ranch_shot_exr_dir}")
        return

    log_info("Test mode ON" if is_test_mode else "Live mode ON")

    for root, dirs, files in os.walk(ranch_shot_exr_dir):
        for file_name in files:
            if file_name.lower().endswith(".exr"):
                src_file = os.path.join(root, file_name)
                # Build the new path (replace the ranch prefix with local_exr_copy_dir)
                dst_file = src_file.replace(ranch_out_exr_dir, local_exr_copy_dir, 1)

                if is_test_mode:
                    log_info(f"[TEST] mkdir: {os.path.dirname(dst_file)}")
                    log_info(f"[TEST] copy: {src_file} -> {dst_file}")
                    if delete_local_exr_after_copy:
                        log_info(f"[TEST] delete: {src_file}")
                    else:
                        log_info(f"[TEST] DELETE EXR AFTER COPY NOT ACTIVATED - SKIP: {src_file}")
                else:
                    try:
                        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                        log_info(f"Copied: {src_file} -> {dst_file}")
                        if delete_local_exr_after_copy:
                            try:
                                os.remove(src_file)
                                log_info(f"Deleted: {src_file}")
                            except PermissionError:
                                log_error(f"Perm denied: {src_file}")
                            except Exception as e:
                                log_error(f"Error deleting '{src_file}': {e}")
                        else:
                            log_info(f"DELETE_LOCAL_EXR_AFTER_COPY is FALSE. Skip delete: {src_file}")
                    except PermissionError:
                        log_error(f"Perm denied copying '{src_file}' -> '{dst_file}'.")
                    except FileNotFoundError:
                        log_error(f"File/path missing '{src_file}' -> '{dst_file}'.")
                    except OSError as e:
                        log_error(f"OS error copying '{src_file}' -> '{dst_file}': {e}")
                    except Exception as e:
                        log_error(f"Unexpected error copying '{src_file}' -> '{dst_file}': {e}")

    log_info("Script finished.")

# --------------------------------------------------------------------------
# MAIN SCRIPT
# --------------------------------------------------------------------------

# Parse arguments safely, reconstructing settingsFile if it has spaces
startFrame = int(sys.argv[1])
endFrame = int(sys.argv[2])

# settingsFile may be split if it contains spaces; join from argv[3] onward
settingsFile = " ".join(sys.argv[3:])

# Resolve environment variables
husk_path = os.getenv("HUSK_PATH")
prism_husk_path = os.getenv("PRISM_DEADLINE_HUSK_PATH")

# Determine executable path
executable = husk_path
if not executable or not os.path.exists(executable):
    executable = prism_husk_path
    if not executable or not os.path.exists(executable):
        raise Exception(
            "The Husk render executable is not defined or doesn't exist.\n"
            f"HUSK_PATH: {husk_path}\n"
            f"PRISM_DEADLINE_HUSK_PATH: {prism_husk_path}\n"
            "Use \"HUSK_PATH\" or \"PRISM_DEADLINE_HUSK_PATH\" "
            "environment variable to specify a valid path."
        )

# Debug prints
print(f"__file__: {__file__}")
print(f"os.path.dirname(__file__): {os.path.dirname(__file__)}")
print(f"settingsFile: {settingsFile}")

# Build the full path to the settings JSON file
full_settings_path = os.path.join(os.path.dirname(__file__), settingsFile)
print(f"Full path to settings file: {full_settings_path}")

# Load the JSON settings
with open(full_settings_path, "r") as f:
    settings = json.load(f)

renderer = settings["renderer"]
renderSettings = settings["rendersettings"]
imgOutput = settings["outputpath"]
usdFilePath = settings["usdfile"]
frameCount = str(endFrame-startFrame+1)
useTiles = settings.get("useTiles", False)
tilesX = settings.get("tilesX", 1)
tilesY = settings.get("tilesY", 1)
if useTiles:
    tileFrame = int(settings.get("startFrame", 1))
    tileIdx = startFrame - tileFrame
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


usdFilePath = usdFilePath.replace("####", "$F4")

# Setup environment
os.environ["HOUDINI_PACKAGE_DIR"] = "C:/tmp/houdinipackage/"
os.environ["PXR_AR_DEFAULT_SEARCH_PATH"] = (f"{LOCAL_DRIVE_I};{LOCAL_DRIVE_R}")
env_copy = dict(os.environ)

print("HOUDINI_PACKAGE_DIR:", os.environ["HOUDINI_PACKAGE_DIR"])
print("ENV keys:", list(env_copy.keys()))

computer_name = os.getenv('COMPUTERNAME', '')
if computer_name.startswith("RANCH") and "nocache" not in usdFilePath: 
    usdFilePath, imgOutput, env_copy = remap_ranch_usd_and_output(usdFilePath, imgOutput, env_copy)
else:
    print(f"No ranch path mapping for {computer_name}")

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
    "--exrmode", "1",
    "--autocrop", "C,A",
]

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

print("command args: %s" % (args))
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
    # If on RANCH, copy EXRs back to network
    if computer_name.startswith("RANCH"):
        print("Start copying EXRs back to network...")
        shot_dir = os.path.dirname(imgOutput)
        copy_exr_from_ranch_to_network(
            ranch_shot_exr_dir=shot_dir,
            ranch_out_exr_dir=RANCH_OUT_EXR_DIR,
            is_test_mode=IS_EXR_COPY_ONLY_TEST_MODE,
            delete_local_exr_after_copy = DELETE_LOCAL_EXR_AFTER_COPY # Set False to do real copy & delete
        )
    else:
        print("Skipping EXR copy-back")
    
    print("task completed successfully")