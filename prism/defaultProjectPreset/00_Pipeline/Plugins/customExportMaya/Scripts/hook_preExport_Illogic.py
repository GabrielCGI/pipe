import sys
from importlib import reload

#------------ import splitVariantRig et creation de ses variable ------------
SPLIT_VARIANT_RIG_PATH = "R:/pipeline/pipe/maya/scripts"
ENABLE_SPLIT_VARIANT_RIG = True
sys.path.append(SPLIT_VARIANT_RIG_PATH)

try:
    import split_variants_rig as svr #type: ignore
except ImportError:
    ENABLE_SPLIT_VARIANT_RIG = False

# add JIPEBOX WG_ILOGIC
JIPEBOX_WG_ILOGIC = "R:/tmp/jipe/WG_ILOGIC"
if JIPEBOX_WG_ILOGIC not in sys.path:
    sys.path.append( JIPEBOX_WG_ILOGIC )


def main(core_prism, output_name):
    print(core_prism) # core de prism
    print(output_name) # fichier d'export du product
    # pass

    print ("* HOOK: PRE_EXPORT_ILLOGIC")
    scene_path = core_prism.getCurrentFileName()
    if '\\Rigging\\' not in scene_path:
        return

    else:
        print ("*   MAYA RIGGING CONTEXT")
        
        # ///////////////////////////////// rigProductCleaner ///////////////////////
        #cleanRig Test ----------------------------------------
        try:
            print ("//"*50)
            # importing des ref -------------
            import maya.cmds as cmds
            
            refL = cmds.file(q=True, r=True)  # list of reference file paths
            for ref in refL:
                try:
                    cmds.file(ref, importReference=True, )
                except Exception as err:
                    print(f"! Failed to import: {err}") 

            # # execution du script distant -------------
            # execFileP = "R:/tmp/jipe/WG_ILOGIC/specifics/convert_oldShader_to_lambert_ani_v006.py"
            # exec( open(execFileP).read(),globals())
            import specifics.rigProductCleaner_v001 as rpc #type: ignore
            reload(rpc)
            rpcI = rpc.rigProductCleaner(RENDERGPN="geo")
            rpcI.exec()
            
        except Exception as err:
            print ("*rigProductCleaner(): ERROR(S) Dude! :")
            print (f"* {err}")
            print ("//"*50)
        # ////////////////////////////////////////////////////////////////////////////


    
    #créer est spliter tous les différents variants entre eux pour créer un product (export) pour que variant pour avoir dans son rig uniquement le variant en question
    if ENABLE_SPLIT_VARIANT_RIG:
        #Exécuter le script uniquement dans les scènes de Rigging qui sont dans le département rigging et la task rigging 
        scene_path = core_prism.getCurrentFileName()
        if '\\Rigging\\' not in scene_path:
            return
        
        spliter_variant = svr.main(core_prism, scene_path)
        spliter_variant.execAfterImportReference()