nuke.pluginAddPath ('R:/nukeGizmo')
nuke.pluginAddPath ('R:/pipeline/pipe/nuke/script')

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


nuke.pluginAddPath("R:\nukeGizmo\NukeSurvivalToolkit_publicRelease-master\NukeSurvivalToolkit")
# >>>PrismStart
import nuke

if ((not nuke.env["studio"]) or nuke.env["indie"]) and not nuke.env.get("gui"):
    if "pcore" in locals():
        nuke.message("Prism is loaded multiple times. This can cause unexpected errors. Please clean this file from all Prism related content:\n\n%s\n\nYou can add a new Prism integration through the Prism Settings dialog" % __file__)
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
