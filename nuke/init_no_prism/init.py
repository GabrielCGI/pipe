## Nuke Init for Illogic
## ValDo Edit 240903
import nuke
import nukescripts
import os
os.environ["OFX_PLUGIN_PATH"] = "D:/OFX_local"

#print("---------- WARNING : BETA MODE ACTIVATED ---------")



if nuke.NUKE_VERSION_MAJOR==12:
    print("Nuke Init as version 12...")
    
    ### -------------------------------------------------------------------------------------------
    ### ----------------------------------     Nuke 13      ---------------------------------------
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
    nuke.pluginAddPath("R:/nukeGizmo/stamps")


    print("End Nuke Init as version 12!")

if nuke.NUKE_VERSION_MAJOR >= 13:

    #ATTENTION A NE PAS UTILISER DE FORMAT f{} -> FAIS CRASHER NUKE 12 !!!!
    nuke_version = str(nuke.NUKE_VERSION_MAJOR)+"."+str(nuke.NUKE_VERSION_MINOR)

    print("Nuke Init as version 13+ ...\n")
    # ### -------------------------------------------------------------------------------------------
    # ### ----------------------------------     Nuke 13-15+      --------------------------------------
    # ### -------------------------------------------------------------------------------------------

    # >>>PrismStart


    # <<<PrismEnd
    nuke.pluginAddPath("R:/pipeline/networkInstall/Nuke/nuke15+_configs/NukeSurvivalToolkit/")
    nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/gizmos')
    nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/ToolSets')
    nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/scripts')
    nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/icons')
    #nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/plugins')
    nuke.pluginAddPath('R:/pipeline/pipe/nuke/script')
    nuke.pluginAddPath("R:/pipeline/networkInstall/Nuke/nuke15+_configs/plugins/MagicDefocus2_v1.0.3")
    nuke.pluginAddPath("R:/pipeline/networkInstall/Nuke/nuke15+_configs/plugins/stamps")
    nuke.pluginAddPath("R:/pipeline/networkInstall/Nuke/nuke15+_configs/gizmos/Deep2VP_v40")
    nuke.pluginAddPath("R:/pipeline/networkInstall/Nuke/nuke15+_configs/gizmos/pixelfudger3")
    nuke.pluginAddPath("R:/pipeline/networkInstall/Nuke/nuke15+_configs/scripts/nukeToPack/", 'nukeToPack/icons')
    nuke.pluginAddPath('R:/pipeline/networkInstall/Nuke/nuke15+_configs/gizmos/aeRefractor')

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

