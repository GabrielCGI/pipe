# This script will be executed after the execution of an export state in the Prism State Manager.
# You can use this file to define project specific actions, like manipulating the outputfiles.

# Example:

# If the main function exists in this script, it will be called.
# The "kwargs" argument is a dictionary with usefull information about Prism and the current export.
#import usdApi
from importlib import reload
import socket
import sys

MODULES_SEARCH_PATH = ["R:/pipeline/pipe/prism/ranch_cache_scripts", "R:/pipeline/pipe/prism/proxyShaders", "R:/pipeline/pipe/prism/USDToolBox_pck", "R:/pipeline/pipe/maya/scripts"]
for customPath in MODULES_SEARCH_PATH:
    if not customPath in sys.path:
        sys.path.append(customPath)



def main(*args, **kwargs):
    core = kwargs["core"]
    comment = core.getStateManager().publishComment
    if comment == 'noHook':
        print('Hook deactivated')
        return
    
    
    elif core.appPlugin.pluginName == "Maya":
        path = kwargs["outputpath"]
        if not "\Export\_layer_anm_" in path:
            return
        
        #utilise un package qui permet de parcourir le fichier anm exporter pour pouvoir clean le layer d'anim comme on le veux / de plus on fait torner l'inherite class a se moment la
        import usd_chaser
        usd_chaser.chaser_layer_anim(kwargs["outputpath"])
        usd_chaser.create_inheriteClass(core)


    elif core.appPlugin.pluginName == 'Houdini':
        # import hou
        # import importlib
        
        # if not hou.isUIAvailable():
        #     print("Houdini is not in GUI mode. Skipping ranchExporter in postRender.")
        #     return
        # else: 
            # print("Houdini is in GUI mode. Starting ranchExporter in postRender.")
            #import threading
            #import ranchExporter
            #importlib.reload(ranchExporter)
            
            # import socket
            # hostname = socket.gethostname()
            # if hostname in ['RACOON-01']:
            #     print(f'Currently debugging on {hostname}')
            #     usdpath = ranchExporter.getUsdPath(kwargs)
            #     ranchExporter.parseAndCopyToRanchDev(usdpath, kwargs)
                
            #     # thread = threading.Thread(target=ranchExporter.parseAndCopyToRanchDev, args=(usdpath, kwargs,))
            #     # thread.start()
            #     return
            
            #usdpath = ranchExporter.getUsdPath(kwargs)
            #thread = threading.Thread(target=ranchExporter.parseAndCopyToRanch, args=(usdpath, kwargs,))
            #thread.start()



        #create proxy variant in the mtl.usdc file for props and assets

        file = kwargs["outputpath"]
        scenefile = kwargs["scenefile"].split("\\")
        stateManager = kwargs["state"]

        if stateManager.getRenderNode().type().name() == "componentoutput" and str(stateManager.getRenderNode()) in scenefile:
            folder = "/".join(file.split("/")[:-1])

            print(socket.gethostname())
            print("-----delete roughness preview in  mtl.usdc------------------")
            try:
                import editpreviewUSD as epv
                epv.edit_preview_USD(folder)
                print("delete roughness terminée")
            
            except Exception as e:
                print(f"error script {e}")
                pass
