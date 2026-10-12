import logging



logger = logging.getLogger("IllogicPlugin."+__name__)



def main(*args, **kwargs):
    logger.info("START: file Hook postExport")
    core = kwargs["core"]
    comment = core.getStateManager().publishComment
    if comment == 'noHook':
        logger.info('Hook deactivated')
        logger.info("END: file Hook postExport")
        return
    
    
    elif core.appPlugin.pluginName == "Maya":
        path = kwargs["outputpath"]
        if "\Export\_layer_anm_" not in path:
            return
        
        logger.info("import and start usd_chaser")
        #utilise un package qui permet de parcourir le fichier anm exporter pour pouvoir clean le layer d'anim comme on le veux / de plus on fait torner l'inherite class a se moment la
        import usd_chaser #type: ignore
        usd_chaser.chaser_layer_anim(kwargs["outputpath"])
        usd_chaser.create_inheriteClass(core)
        logger.info("end usd_chaser")


    elif core.appPlugin.pluginName == 'Houdini':
        scenefile = kwargs["scenefile"].split("\\")
        stateManager = kwargs["state"]
        file = kwargs["outputpath"]

        if stateManager.getRenderNode().type().name() == "componentoutput" and str(stateManager.getRenderNode()) in scenefile:
            logger.info("-----delete roughness preview in  mtl.usdc------------------")
            folder = "/".join(file.split("/")[:-1])
            try:
                import usd_supp_previewtexture #type: ignore
                usd_supp_previewtexture.edit_preview_USD(folder)
                logger.info("delete roughness terminée")
            
            except Exception as e:
                logger.error(f"error script {e}")
                pass
        
    logger.info("END: file Hook postExport")
