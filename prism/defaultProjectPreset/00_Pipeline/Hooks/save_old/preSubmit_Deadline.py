import socket
# try:
#     import hou #type: ignore
#     HOUDINI_IMPORT = True
# except:
#     HOUDINI_IMPORT = False
import sys
import os


DEBUG_LIST = ["FOX-04", "FALCON-01"]
DEBUG = False
VARIABLE_TO_DELETE = [
    "KARMA_XPU_MAX_LIGHTING_TEXTURE_RES",
    "KARMA_XPU_MAX_SHADER_TEXTURE_RES",
    "HOUDINI_BUFFEREDSAVE"
]

def main(origin, Settings, pluginInfos, arguments):
    #object Prism_Deadline = origin       is a object
    #data send to Deadline = Settings     is a dict
    #husk_settings.json = pluginInfos     is a dict
    #data job_info.job = arguments        is a dict

    core = origin.core
    if core.appPlugin.pluginName != "Houdini": # or not HOUDINI_IMPORT
        return
    
    print("----------------------- Custom parameter Deadline -----------------------")
    #trouver toute les environments variables qui bride le mapping des textures
    AllEnvVariable = []
    copySettings = Settings.copy()
    print(copySettings)
    for key, value in copySettings.items():
        if key.startswith("EnvironmentKeyValue"):
            should_skip = False
            for ban_variable in VARIABLE_TO_DELETE:
                if ban_variable in value:
                    should_skip = True
                    break
            if not should_skip:
                AllEnvVariable.append(value)
            del Settings[key]

    # add specifics environnments variables
    AllEnvVariable.append("KARMA_XPU_OPTIX_SPARSE_TEXTURES=1")
    
    for i, data in enumerate(AllEnvVariable):
        Settings[f"EnvironmentKeyValue{i}"] = data
    
    #--------------------------------------------------- DEBUG --------------------------------------
    if socket.gethostname() in DEBUG_LIST and DEBUG:
        sys.path.append("R:/pipeline/networkInstall/python_shares/python311_debug_pkgs/Lib/site-packages")
        from debug import debug # type: ignore
        debug.debug()
        debug.debugpy.breakpoint()
    #--------------------------------------------------- DEBUG --------------------------------------

    if 'ILLOGIC_TEMP_NODE' not in os.environ:
        return

    dataNodeExport = eval(os.environ.get("ILLOGIC_TEMP_NODE")) # environement variable creer dans le script preRender
    if "high_prio" not in Settings["Name"]:
        del os.environ['ILLOGIC_TEMP_NODE']
    if not dataNodeExport:
        return
    
    res, result = getOptimisation(dataNodeExport, Settings["Name"])
    if result:
        Settings["Comment"] = Settings["Comment"] + "_OPTI"
        Settings["Name"] = Settings["Name"] + f"__OPTI{res}"
        editVarEnviron(Settings, res, i)
        name = Settings["Name"]
        print(f"add environment variable for the job:\n   ---> {name}\n   ---> resolution set: {res}\n")



def editVarEnviron(Setting, res, i):
    for value in [f"KARMA_XPU_MAX_LIGHTING_TEXTURE_RES={str(int(res)*2)}", f"KARMA_XPU_MAX_SHADER_TEXTURE_RES={res}"]:
        i += 1
        Setting[f"EnvironmentKeyValue{i}"] = value


def getOptimisation(dataNodeForDeadLine, Name):
    default_res = 1024
    layer = None
    for key in dataNodeForDeadLine:
        if key in Name:
            layer = key
            break
    
    if not layer:
        return None, False
    
    resolution = dataNodeForDeadLine[layer]["OPTI"]
    
    if layer == "VOLUME" or layer == "QC" or layer == "FOGPAINT":
        if not resolution:
            resolution = default_res
    
    if not resolution or "no_opti" == resolution:
        return None, False

    return resolution, True