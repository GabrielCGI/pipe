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
    for key, value in copySettings.items():
        if key.startswith("EnvironmentKeyValue"):
            if not "KARMA_XPU_MAX_LIGHTING_TEXTURE_RES" in value and not "KARMA_XPU_MAX_SHADER_TEXTURE_RES" in value and not "HOUDINI_BUFFEREDSAVE" in value:
                AllEnvVariable.append(value)
            del Settings[key]


    for i, data in enumerate(AllEnvVariable):
        Settings[f"EnvironmentKeyValue{i}"] = data
    

    #--------------------------------------------------- DEBUG --------------------------------------
    if socket.gethostname() in DEBUG_LIST and DEBUG:
        sys.path.append("R:/pipeline/networkInstall/python_shares/python311_debug_pkgs/Lib/site-packages")
        from debug import debug
        debug.debug()
        debug.debugpy.breakpoint()
    #--------------------------------------------------- DEBUG --------------------------------------

    if not 'ILLOGIC_TEMP_NODE' in os.environ:
        return

    dataNodeExport = eval(os.environ.get("ILLOGIC_TEMP_NODE")) # environement variable creer dans le script preRender
    if not "high_prio" in Settings["Name"]:
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


    #force env var for foundry license 
    if jobInfos["Plugin"] == "Nuke":
        origin.addEnvironmentItem(jobInfos, "foundry_LICENSE", "4101@rlm-illogic")
        # force deadline license limit for Nuke
        jobInfos["LimitGroups"] = "nukelimit"



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