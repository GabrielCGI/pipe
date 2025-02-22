name = "ChangeHuskRenderCommand"
classname = "ChangeHuskRenderCommand"


class ChangeHuskRenderCommand:
    def __init__(self, core):
        self.core = core
        self.version = "v1.1.0"
        
        if self.core.appPlugin.pluginName not in ["Houdini", "Maya"]:
              return
          
        # check if USD plugin is loaded
        dlPlugin = self.core.getPlugin("USD")
        if dlPlugin:
            # if yes, patch the function
            self.applyPatch(dlPlugin)

        # register callback in case the USD plugin will be loaded later on
        # this is important if the plugin gets loaded later on during the startup or manually by the user
        self.core.registerCallback(
            "pluginLoaded", self.onPluginLoaded, plugin=self
        )

    def onPluginLoaded(self, plugin):
        # check if the loaded plugin is the USD plugin and if yes apply the patch
        if plugin.pluginName == "USD":
            self.applyPatch(plugin)

    def applyPatch(self, plugin):
        print("Patching HUSK Render Command to add path remapping for Ranch - autocrop mode")
        # apply the monkeypatch to the "getHuskRenderScript" function of the USD plugin
        self.core.plugins.monkeyPatch(plugin.getHuskRenderScript, self.getHuskRenderScript, self, force=True)

    def getHuskRenderScript(self):

        #NOTES: 
        # The RANCH cache path need 8 "\" to work, it's a lot but it's needed...
        # C'est deux anti-slash échapé 2 fois 2x2x2 = 8 
        script = """
import os
import sys
import subprocess
import shutil

renderer = sys.argv[6]
renderSettings = sys.argv[5]
imgOutput = sys.argv[4]
usdFilePath = sys.argv[3]
endFrame = int(sys.argv[2])
startFrame = int(sys.argv[1])

executable = os.getenv("HUSK_PATH")
if not executable or not os.path.exists(executable):
    executable = os.getenv("PRISM_DEADLINE_HUSK_PATH")
    if not executable or not os.path.exists(executable):
        raise Exception("The Husk render executable is not defined or doesn't exist. Use \\"HUSK_PATH\\" or \\"PRISM_DEADLINE_HUSK_PATH\\" environment varialbe to specify a path.")


def readStdout(proc):
    while True:
        line = proc.stdout.readline()
        line = line.decode("utf-8", errors="ignore")
        if "ALF_PROGRESS" in line:
            print("Progress: %s" % line.replace("ALF_PROGRESS ", ""))

        if line == '' and proc.poll() is not None:
            break

        print(line)

def copy_COP_textures(src_path, dst_path):
    # Get the parent directories of the src_path and dst_path.
    # src_parent is where we will look for textures directories.
    src_parent = os.path.dirname(os.path.abspath(src_path))
    dst_parent = os.path.dirname(os.path.abspath(dst_path))

    drive, tail = os.path.splitdrive(src_parent)
    tail = tail.lstrip("\\/")
    
    # Build the ranchcache directory
    ranchcache_dir = os.path.join("I:/ranch_cache/I", tail)

    # Iterate over all items in the src_parent directory.
    for item in os.listdir(src_parent):
        item_path = os.path.join(src_parent, item)
        # Check if item is a directory and ends with '.textures'
        if os.path.isdir(item_path) and item.endswith('.textures'):
            target_dir = os.path.join(dst_parent, item)
            if not os.path.exists(target_dir):
                print(f"Copying textures directory '{item_path}' to '{target_dir}'")
                try:
                    shutil.copytree(item_path, target_dir)
                    print("Copy completed successfully.")
                except Exception as e:
                    print(f"An error occurred while copying '{item_path}': {e}")
            else:
                print(f"Directory '{target_dir}' already exists. Skipping copy.")
            target_dir_ranch = os.path.join(ranchcache_dir, item)    
            if not os.path.exists(target_dir_ranch ):
                print(f"Copying textures directory '{item_path}' to '{target_dir_ranch }'")
                try:
                    shutil.copytree(item_path, target_dir_ranch )
                    print("Copy completed successfully.")
                except Exception as e:
                    print(f"An error occurred while copying '{item_path}': {e}")
            else:
                print(f"Directory '{target_dir_ranch}' already exists. Skipping copy.")

def convert_path(original_path):
    # Define prefixes to replace
    prefixes_to_replace = {
        "I:/": "\\\\\\\\RANCH-111\\\\ranch_cache\\\\I\\\\",
        "R:/": "\\\\\\\\RANCH-111\\\\ranch_cache\\\\R\\\\"
    }
    
    # Replace the prefix if it matches any in the dictionary
    for prefix, replacement in prefixes_to_replace.items():
        if original_path.startswith(prefix):
            return original_path.replace(prefix, replacement, 1 )
    
    return "Path does not match expected patterns."

def convert_path_local_ranch(original_path):
    # Define prefixes to replace
    prefixes_to_replace = {
        "I:/": "I:/ranch_cache/I/",
    }
    
    # Replace the prefix if it matches any in the dictionary
    for prefix, replacement in prefixes_to_replace.items():
        if original_path.startswith(prefix):
            return original_path.replace(prefix, replacement, 1 )
    
    return "Path does not match expected patterns."

usdFilePath = usdFilePath.replace("####", "$F4")



env_copy = dict(os.environ)
env_copy["HOUDINI_PACKAGE_DIR"] = "C:/tmp/houdinipackage/"
os.environ["HOUDINI_PACKAGE_DIR"] = "C:/tmp/houdinipackage/"
env_vars = {key: os.environ[key] for key in os.environ.keys()}

print ("Houdini package modificed")
print (os.environ["HOUDINI_PACKAGE_DIR"])
print(env_vars)



computer_name = os.getenv('COMPUTERNAME', '')  # Get the computer name
if computer_name.startswith("RANCH") and "nocache" not in usdFilePath :

    print("Ranch detected. Remapping USD path... (add nocache to prism lop render node name to prevent it)")



    usdFilePathRemaped = convert_path(usdFilePath)
    local_ranch_usdFilePath = convert_path_local_ranch(usdFilePath)
    print(f"Usd file path remap for {usdFilePath} to {usdFilePathRemaped}")
    print(f"Usd file path remap for {usdFilePath} to {local_ranch_usdFilePath}")
    if not os.path.exists(usdFilePathRemaped):
        print(f"USD does not exist: {usdFilePathRemaped}")
        
        if os.path.exists(usdFilePath):
            print(f"but USD exists: {usdFilePath}")
            try:
                dest_dir = os.path.dirname(usdFilePathRemaped)
                os.makedirs(dest_dir, exist_ok=True)
                print("dir created")
                shutil.copy2(usdFilePath, usdFilePathRemaped)
                print(f"Copied from {usdFilePath} to {usdFilePathRemaped}")
            except Exception as e:
                print(f"Error copying file: {e}")
        else:
            print(f"Neither file exists: {usdFilePathRemaped} and {usdFilePath}")
    else:
        print(f"USD already exists: {usdFilePathRemaped}, no need to copy.")
    if not os.path.exists(local_ranch_usdFilePath):
        print(f"USD does not exist: {local_ranch_usdFilePath}")
        
        if os.path.exists(usdFilePath):
            print(f"but USD exists: {usdFilePath}")
            try:
                dest_dir = os.path.dirname(local_ranch_usdFilePath)
                os.makedirs(dest_dir, exist_ok=True)
                print("dir created")
                shutil.copy2(usdFilePath, local_ranch_usdFilePath)
                print(f"Copied from {usdFilePath} to {local_ranch_usdFilePath}")
            except Exception as e:
                print(f"Error copying file: {e}")
        else:
            print(f"Neither file exists: {local_ranch_usdFilePath} and {usdFilePath}")
    else:
        print(f"USD already exists: {local_ranch_usdFilePath}, no need to copy.")

    copy_COP_textures(usdFilePath,usdFilePathRemaped)

    usdFilePath = usdFilePathRemaped 

    # Add specific actions for RANCH nodes here
else:
    print(f"No need for remapping for: {computer_name}")
    # Add specific actions for other machines here

args = [
    executable,
    usdFilePath,
    "--output",
    imgOutput,
    "--frame",
    str(startFrame),
    "--frame-count",
    str(endFrame-startFrame+1),
    "--renderer",
    renderer,
    "--verbose",
    "aC6",
    "--settings",
    renderSettings,
    "--exrmode",  # add or change command line arguments here
    "1",
    "--autocrop",
    "C,A",
#   "--windows-console",
#    "wait",
]

if len(sys.argv) > 7:
    camera = sys.argv[7]
    if camera:
        args += ["--camera", camera]

if len(sys.argv) > 9:
    try:
        width = int(sys.argv[8])
        height = int(sys.argv[9])
    except:
        width = height = None

    if width and height:
        args += ["--res", str(width), str(height)]

print("command args: %s" % (args))
p = subprocess.Popen(args, stdout=subprocess.PIPE, env=env_copy)
readStdout(p)

lastFrame = imgOutput.replace("$F4", "%04d" % (endFrame))
if p.returncode:
    raise RuntimeError("renderer exited with code %s" % p.returncode)
elif not os.path.exists(lastFrame):
    raise RuntimeError("expected output doesn't exist %s" % (lastFrame))
else:
    print("task completed successfully")
"""
        return script
