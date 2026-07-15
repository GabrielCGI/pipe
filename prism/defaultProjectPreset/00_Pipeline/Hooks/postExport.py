import socket
import sys

MODULES_SEARCH_PATH = ["R:/pipeline/pipe/prism/USDToolBox_pck"]
for customPath in MODULES_SEARCH_PATH:
    if customPath not in sys.path:
        sys.path.append(customPath)



def main(*args, **kwargs):
    core = kwargs["core"]
    comment = core.getStateManager().publishComment
    if comment == 'noHook':
        print('Hook deactivated')
        return
    
    
    elif core.appPlugin.pluginName == "Maya":
        path = kwargs["outputpath"]
        if "\Export\_layer_anm_" not in path:
            return
        
        #utilise un package qui permet de parcourir le fichier anm exporter pour pouvoir clean le layer d'anim comme on le veux / de plus on fait torner l'inherite class a se moment la
        import usd_chaser
        usd_chaser.chaser_layer_anim(kwargs["outputpath"])
        usd_chaser.create_inheriteClass(core)


    elif core.appPlugin.pluginName == 'Houdini':

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
        