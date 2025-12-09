import socket
import time
import sys
import os



#------------ import sanitycheck et creation de ses variable ------------
SANITYCHECK_PATH = "R:/pipeline/pipe_public/sanitycheck"
ENABLE_SANITY_CHECK = True
sys.path.insert(0, SANITYCHECK_PATH)
try:
    import sanitycheck
except:
    ENABLE_SANITY_CHECK = False

try:
    YAML_LOCATION = os.environ['SANITY_CHECK_CONFIG']
except:
    YAML_LOCATION = "None"


#------------ import splitVariantRig et creation de ses variable ------------
SPLIT_VARIANT_RIG_PATH = "R:/pipeline/pipe/maya/scripts"
ENABLE_SPLIT_VARIANT_RIG = True
sys.path.append(SPLIT_VARIANT_RIG_PATH)
try:
    import split_variants_rig as svr
except Exception as e:
    print(e)
    ENABLE_SPLIT_VARIANT_RIG = False



def main(*args):
    core = args[0].core
    if ENABLE_SANITY_CHECK:
        args = (*args, YAML_LOCATION)
        res = sanitycheck.main(*args)
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
        if not 'Rigging\\Rigging' in scene_path:
            return
        
        spliter_variant = svr.main(core, scene_path)
        spliter_variant.passPrePublish()
        if not spliter_variant.result:
            print('Cancel publish')
            return {"cancel": True}
    else:
        print("marche pas ")
    