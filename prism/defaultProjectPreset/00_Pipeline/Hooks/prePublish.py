import logging
import time
import os



logger = logging.getLogger("IllogicPlugin."+__name__)

#------------ import sanitycheck et creation de ses variable ------------
YAML_LOCATION = os.environ.get('SANITY_CHECK_CONFIG', None)
ENABLE_SANITY_CHECK = True
try:
    import sanity_check #type: ignore
except Exception:
    ENABLE_SANITY_CHECK = False

#------------ import splitVariantRig et creation de ses variable ------------
ENABLE_SPLIT_VARIANT_RIG = True
try:
    import rig_split_variants as svr #type: ignore
except Exception:
    ENABLE_SPLIT_VARIANT_RIG = False



def main(*args):
    logger.info('START: file hook prePublish')
    core = args[0].core
    if ENABLE_SANITY_CHECK:
        logger.info('import and start sanity_check')
        args = (*args, YAML_LOCATION)
        res = sanity_check.main(*args)
        if not res:
            logger.info('Cancel publish')
            logger.info('END: file hook prePublish')
            return {"cancel": True}

        popup = core.waitPopup(core, 'Sanity check sucessfully passed.')
        with popup:
            time.sleep(0.5)
        
        logger.info('end sanity_check')



    if core.appPlugin.pluginName != "Maya":
        logger.info('END: file hook prePublish')
        return

    if ENABLE_SPLIT_VARIANT_RIG:
        #executer le script uniquement dans les scene de Rigging qui sont dans le departement rigging et la task rigging 
        scene_path = core.getCurrentFileName()
        if '\\Rigging\\' not in scene_path:
            return
        
        logger.info('import and start rig_split_variants')
        spliter_variant = svr.main(core, scene_path)
        spliter_variant.passPrePublish(autoExport=False)
        if not spliter_variant.result:
            logger.info('Cancel publish')
            logger.info('END: file hook prePublish')
            return {"cancel": True}

        logger.info('end rig_split_variants')

    logger.info('END: file hook prePublish')