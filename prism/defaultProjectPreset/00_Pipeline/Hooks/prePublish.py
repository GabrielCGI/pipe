import time
import os



#------------ import sanitycheck et creation de ses variable ------------
YAML_LOCATION = os.environ.get('SANITY_CHECK_CONFIG', None)
ENABLE_SANITY_CHECK = True
try:
    import sanity_check
except Exception:
    ENABLE_SANITY_CHECK = False




#------------ import splitVariantRig et creation de ses variable ------------
ENABLE_SPLIT_VARIANT_RIG = True
try:
    import rig_split_variants as svr
except Exception:
    ENABLE_SPLIT_VARIANT_RIG = False



def main(*args):
    core = args[0].core
    if ENABLE_SANITY_CHECK:
        args = (*args, YAML_LOCATION)
        res = sanity_check.main(*args)
        if not res:
            print('Cancel publish')
            return {"cancel": True}
        else:
            msg = 'Sanity check sucessfully passed.'
            popup = core.waitPopup(core, msg)
            with popup:
                time.sleep(0.5)


    if core.appPlugin.pluginName != "Maya":
        return

    if ENABLE_SPLIT_VARIANT_RIG:
        #executer le script uniquement dans les scene de Rigging qui sont dans le departement rigging et la task rigging 
        scene_path = core.getCurrentFileName()
        if '\\Rigging\\' not in scene_path:
            return
        
        spliter_variant = svr.main(core, scene_path)
        spliter_variant.passPrePublish(autoExport=False)
        if not spliter_variant.result:
            print('Cancel publish')
            return {"cancel": True}



    else:
        print("marche pas ")
    