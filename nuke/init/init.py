## Nuke Init for Illogic
## ValDo Edit 240903
import nuke
import os

if nuke.NUKE_VERSION_MAJOR==12:
    print("Nuke Init as version 12...")
    ### -------------------------------------------------------------------------------------------
    ### ----------------------------------     Nuke 12      ---------------------------------------
    ### -------------------------------------------------------------------------------------------

    nuke.pluginAddPath ('R:/nukeGizmo')
    nuke.pluginAddPath ('R:/pipeline/pipe/nuke/script')

    import custom_writer
    import cryptomatte_utilities
    import collectFiles
    cryptomatte_utilities.setup_cryptomatte()

    nuke.pluginAddPath('./X_Tools')

    nuke.pluginAddPath('./X_Tools/Icons')
    nuke.pluginAddPath('./X_Tools/Gizmos')


    # DAMIAN BINDER TOOLS
    nuke.pluginAddPath('./Damian_Binder')
    nuke.pluginAddPath('./Damian_Binder/HeatWave')

    nuke.pluginAddPath('./layerShuffler')


    nuke.pluginAddPath("R:/nukeGizmo/NukeSurvivalToolkit_publicRelease-master/NukeSurvivalToolkit")

    print("End Nuke Init as version 12!")

if nuke.NUKE_VERSION_MAJOR>=15:
    print("Nuke Init as version 15+ ...")
    # ### -------------------------------------------------------------------------------------------
    # ### ----------------------------------     Nuke 15+      --------------------------------------
    # ### -------------------------------------------------------------------------------------------

    # >>>PrismStart
    if ((not nuke.env["studio"]) or nuke.env["indie"]) and not nuke.env.get("gui"):
        if "pcore" in locals():
            nuke.message("Prism is loaded multiple times. This can cause unexpected errors. Please clean this file from all Prism related content:/n/n%s/n/nYou can add a new Prism integration through the Prism Settings dialog" % __file__)
        else:
            import os
            import sys

            try:
                from PySide2.QtCore import *
                from PySide2.QtGui import *
                from PySide2.QtWidgets import *
            except:
                from PySide.QtCore import *
                from PySide.QtGui import *

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
                        mod = importlib.import_module(os.path.splitext(os.path.basename(file))[0])
                        mod.Prism_NoQt()
                else:
                    print("a QCoreApplication exists. failed to load Prism")
            else:
                import PrismCore
                pcore = PrismCore.PrismCore(app="Nuke", prismArgs=["noUI"])

    # <<<PrismEnd

    nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/gizmos')
    nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/scripts')
    nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/icons')
    nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/plugins')

    # Setting env var for optical flare : 
    #os.environ["OPTICAL_FLARES_PATH"] = "R:/pipeline/networkInstall/Nuke/nuke15+_configs/plugins/OpticalFlares_Nuke_15.0_Node-Locked_1.0.94/plugin/Windows"
    os.environ["OPTICAL_FLARES_PRESET_PATH"] = r"R:\pipeline\networkInstall\Nuke\nuke15+_configs\plugins\OpticalFlares_Nuke_15.0_Node-Locked_1.0.94\Textures-And-Presets"
    os.environ["OPTICAL_FLARES_VERBOSE_CONSOLE"]="True"

    print("End Nuke Init as version 15+ !")

