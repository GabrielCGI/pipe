## Nuke Init for Illogic
## ValDo Edit 240903
## Pablo Edit 251105

import nuke
import nukescripts
import os
os.environ["OFX_PLUGIN_PATH"] = "D:/OFX_local"

#print("---------- WARNING : BETA MODE ACTIVATED ---------")


# >>>PrismStart
if ((not nuke.env["studio"]) or nuke.env["indie"]) and not nuke.env.get("gui"):
    if "pcore" in locals():
        nuke.message("Prism is loaded multiple times. This can cause unexpected errors. Please clean this file from all Prism related content:/n/n%s/n/nYou can add a new Prism integration through the Prism Settings dialog" % __file__)
    else:
        print(">>>PrismStart\n")
        import os
        import sys

        if nuke.NUKE_VERSION_MAJOR in [13, 15]:
            try:
                from PySide2.QtCore import *
                from PySide2.QtGui import *
                from PySide2.QtWidgets import *
            except:
                    from PySide.QtCore import *
                    from PySide.QtGui import *
                    from PySide.QtWidgets import *
        if nuke.NUKE_VERSION_MAJOR in [16]:
            from PySide6.QtCore import *
            from PySide6.QtGui import *
            from PySide6.QtWidgets import *

        prismRoot = os.getenv("PRISM_ROOT")
        if not prismRoot:
            prismRoot = "C:/Program Files/Prism2"

        scriptDir = os.path.join(prismRoot, "Scripts")
        if scriptDir not in sys.path:
            sys.path.append(scriptDir)

        scriptDir = os.path.join(prismRoot, "PythonLibs", "CrossPlatform")
        if scriptDir not in sys.path:
            sys.path.append(scriptDir)

        qapp = QApplication.instance()
        if not qapp:
            qapp = QApplication(sys.argv)

        if type(qapp) == QCoreApplication:
            if os.getenv("PRISM_NUKE_TERMINAL_FILES"):
                import importlib
                files = os.getenv("PRISM_NUKE_TERMINAL_FILES").split(os.pathsep)
                for file in files:
                    sys.path.append(os.path.dirname(file))
                    try:
                        print("Debug ValDo: %s")%(os.path.basename(file)[0])
                    except:
                        print("Fail to print debug info os.path.basename(file)[0]")
                    mod = importlib.import_module(os.path.splitext(os.path.basename(file))[0])
                    mod.Prism_NoQt()
            else:
                print("a QCoreApplication exists. failed to load Prism")
        else:
            import PrismCore
            pcore = PrismCore.PrismCore(app="Nuke", prismArgs=["noUI"])

# <<<PrismEnd


#ATTENTION A NE PAS UTILISER DE FORMAT f{} -> FAIS CRASHER NUKE 12 !!!!
nuke_version = str(nuke.NUKE_VERSION_MAJOR)+"."+str(nuke.NUKE_VERSION_MINOR)

# >>>Variable Serveur Licence Start
print("Serveur de licence:", os.environ.get('foundry_LICENSE'))   
# <<<Variable Serveur Licence End

print("Nuke Init as version 13+ ...\n")
# ### -------------------------------------------------------------------------------------------
# ### ----------------------------------     Nuke 13-15+      --------------------------------------
# ### -------------------------------------------------------------------------------------------

nuke.pluginAddPath("R:/pipeline/networkInstall/Nuke/nuke15+_configs/NukeSurvivalToolkit/")
nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/gizmos')
nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/ToolSets')
# 'R:/pipeline/networkInstall/Nuke/nuke15+_configs/nuke15+_configs seulement pour que les ToolSets puissent etre loades correctement, lorsque l on pointe sur toolSets cela ne fonctionne pas
nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs')
nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/scripts')
nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/icons')
nuke.pluginAddPath('R:/pipeline/pipe/nuke/cameraMetadata')
#nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/plugins')
nuke.pluginAddPath('R:/pipeline/pipe/nuke/script')
nuke.pluginAddPath("R:/pipeline/networkInstall/Nuke/nuke15+_configs/gizmos/Deep2VP_v40")
nuke.pluginAddPath("R:/pipeline/networkInstall/Nuke/nuke15+_configs/gizmos/pixelfudger3")
nuke.pluginAddPath("R:/pipeline/networkInstall/Nuke/nuke15+_configs/scripts/nukeToPack/", 'nukeToPack/icons')
nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/gizmos/aeRefractor')
nuke.pluginAddPath('R:/devmaxime/dev/nuke/nuke_path/plugins')
nuke.pluginAddPath("R:/pipeline/networkInstall/Nuke/nuke15+_configs/plugins/stamps")

# ### load magic defocus only if nuke 13 ou 16
if nuke.NUKE_VERSION_MAJOR == 13:
    nuke.pluginAddPath("R:/pipeline/networkInstall/Nuke/nuke15+_configs/plugins/MagicDefocus2_v1.0.3")
elif nuke.NUKE_VERSION_MAJOR == 15:
    nuke.pluginAddPath("R:/pipeline/networkInstall/Nuke/nuke15+_configs/plugins/MagicDefocus2_v1.0.3")
else :
    print ("passing magic defocus 2")


# << Start Illogic custom plugins
if nuke.NUKE_VERSION_MAJOR == 13:
    nuke.pluginAddPath("R:/pipeline/networkInstall/Nuke/nuke15+_configs/plugins/custom_illogic/nuke_13")
elif nuke.NUKE_VERSION_MAJOR == 15:
    nuke.pluginAddPath("R:/pipeline/networkInstall/Nuke/nuke15+_configs/plugins/custom_illogic/nuke_15")
# << End Illogic custom plugins 
    
### << Start Optical flare
os.environ["OPTICAL_FLARES_VERBOSE_CONSOLE"]="True"

if(nuke_version=="13.1"):
    
    os.environ["OPTICAL_FLARES_PRESET_PATH"] = r"R:\pipeline\networkInstall\Nuke\nuke15+_configs\OpticalFlares\OpticalFlares_Nuke_13.1_Node-Locked_1.0.9\Textures-And-Presets"

    if nuke.env['gui']:
        print("Nuke 13.1 GUI version")
        nuke.pluginAddPath(r"R:\pipeline\networkInstall\Nuke\nuke15+_configs\OpticalFlares\OpticalFlares_Nuke_13.1_Node-Locked_1.0.9\plugin\Windows")
        os.environ["OPTICAL_FLARES_LICENSE_PATH"] = r"C:\Program Files\Nuke13.1v5"
    else:
        print("Nuke 13.1 FARM version")
        os.environ["OPTICAL_FLARES_NO_GPU"] = "True"
        nuke.pluginAddPath(r"R:\pipeline\networkInstall\Nuke\nuke15+_configs\OpticalFlares\OF_Render_13.1\plugin\Windows")
        os.environ["OPTICAL_FLARES_LICENSE_PATH"] = r"R:\pipeline\networkInstall\Nuke\nuke15+_configs\OpticalFlares\licenses"
        
elif (nuke_version=="15.1"):
    
    # Common Optical flares env
    os.environ["OPTICAL_FLARES_PRESET_PATH"] = r"R:\pipeline\networkInstall\Nuke\nuke15+_configs\OpticalFlares\OpticalFlares_Nuke_15.1_Node-Locked_1.0.94\Textures-And-Presets"
    

    if nuke.env['gui']:
        print("Nuke 15.1 GUI version")
        
        print("\nSetting up Optical Flares for Nuke 15.1\n")
        nuke.pluginAddPath(r"R:\pipeline\networkInstall\Nuke\nuke15+_configs\OpticalFlares\OpticalFlares_Nuke_15.1_Node-Locked_1.0.94\plugin\Windows")
        os.environ["OPTICAL_FLARES_LICENSE_PATH"] = r"C:\Program Files\Nuke15.1v5"

    else:
        print("Nuke 15.1 FARM version")
        os.environ["OPTICAL_FLARES_NO_GPU"] = "True"
        nuke.pluginAddPath(r"R:\pipeline\networkInstall\Nuke\nuke15+_configs\OpticalFlares\OF_Render_15.1\plugin\Windows")
        os.environ["OPTICAL_FLARES_LICENSE_PATH"] = r"R:\pipeline\networkInstall\Nuke\nuke15+_configs\OpticalFlares\licenses"
        # 
    # Setting env var for optical flare : 
    

else:
    print("something went wrong with optical flare, maybe you should install the minor version of it, in your case : " + nuke_version)

    ### End Optical flare >>

    nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/plugins')
    



    print("End Nuke Init as version 13+ !\n\n")


## edit 2025.09.12  (YY.MM.DD)
##  set some node defalut configs

##  write nodes

nuke.knobDefault('Write.exr.compression', '8')
nuke.knobDefault('Write.exr.dw_compression_level', '85')
nuke.knobDefault('Write.exr.interleave', '2')

##  write nodes

print("End Nuke Init as version 13+")