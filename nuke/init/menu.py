#
#
#  Copyright (c) 2014, 2015, 2016, 2017 Psyop Media Company, LLC
#  See license.txt
#
# Pablo Edit 251105

# coding: utf-8
import sys
import nuke
import nukescripts
import os.path

print('Version 251105')

if nuke.NUKE_VERSION_MAJOR==12:
    print("Loading Nuke Menu as version 12...")
    ### -------------------------------------------------------------------------------------------
    ### ----------------------------------     Nuke 12      ---------------------------------------
    ### -------------------------------------------------------------------------------------------

    print('Version 13')

    from nukescripts import panels
    import LayerShuffler
    from auto_comp.AutoComp import AutoComp
    # from auto_compV2.AutoComp import AutoComp 
    import auto_compV2.AutoComp as auto_comp_v2
    from nuke_scanner.NukeScanner import NukeScanner
    from nuke_scanner import select_unconnected_read
    from nuke_scanner import nuke_delete
    import nuke_scanner_old.NukeScanner as NukeScannerOld
    import nuke_scanner_old.nuke_delete as nuke_delete_old

    from crypto import crypto_extract

    import cryptomatte_utilities
    import MultiChannelCombine
    import nukeReadLoader
    import noice_aov_print
    import DeadlineNukeClient

    panels.registerWidgetAsPanel("LayerShuffler.LayerShuffler", "Layer Shuffler", "LayerShufflerPanelId")
    panels.registerWidgetAsPanel("AutoComp", 'AutoComp', 'illogic_studios.auto_comp')
    panels.registerWidgetAsPanel("auto_comp_v2.AutoComp", 'AutoComp V2', 'illogic_studios.autocompV2')

    cryptomatte_utilities.setup_cryptomatte_ui()
    collectMenu = nuke.menu("Nodes").addMenu("Collect_Files")
    collectMenu.addCommand('Collect Files', 'collectFiles.collectFiles()')
    collectMenu.addCommand('Help', 'collectFiles.myBlog()')

    bloomMenu = nuke.menu("Nodes").addMenu("bloom","bloom.png")
    bloomMenu.addCommand("Delete unused render", "NukeScanner().run()")
    bloomMenu.addCommand("Delete unused render (OLD)", "NukeScannerOld.NukeScanner().run()")
    bloomMenu.addCommand("Truly Delete unused render", "nuke_delete.run()")
    bloomMenu.addCommand("Truly Delete unused render (OLD)", "nuke_delete_old.run()")
    bloomMenu.addCommand("Select unused read nodes", "select_unconnected_read.run()")
    bloomMenu.addCommand("Extract crypto as mask", "crypto_extract.run()", "Ctrl+Shift+E")
    bloomMenu.addCommand("Localization policy on", "set_localization_policy_on()")

    toolbar = nuke.toolbar("Nodes")
    toolbar.addMenu("VideoCopilot", icon="VideoCopilot.png")
    toolbar.addCommand( "VideoCopilot/OpticalFlares", "nuke.createNode('OpticalFlares')", icon="OpticalFlares.png")


    menubar = nuke.menu("Nuke")
    tbmenu = menubar.addMenu("&Thinkbox")
    tbmenu.addCommand("Submit Nuke To Deadline", DeadlineNukeClient.main, "")

    toolbar = nuke.toolbar("Nodes")
    toolbar.addMenu("VideoCopilot", icon="VideoCopilot.png")
    toolbar.addCommand( "VideoCopilot/OpticalFlares", "nuke.createNode('OpticalFlares')", icon="OpticalFlares.png")

    # DAMIAN BINDER TOOLS
    toolbar = nuke.toolbar("Nodes")
    m = toolbar.addMenu("DamianBinder", icon="DamianBinderNukeLogo.png")
    m.addCommand("HeatWave", "nuke.createNode(\"HeatWave\")", icon="HeatWave_Icon.png")# >>>PrismStart

    def set_localization_policy_on():
        for node in nuke.allNodes('Read'):
            # Check if the localizationPolicy knob exists
            if 'localizationPolicy' in node.knobs():
                node['localizationPolicy'].setValue('on')

    def create_write_local():
        write_node = nuke.createNode('Write')

        # Create custom name with increment : WriteLocal1, WriteLocal2 ...
        base_name = "WriteLocal"
        i = 1
        while nuke.exists(base_name + str(i)):
            i += 1

        # Set parameters
        write_node['name'].setValue(base_name + str(i))
        write_node['tile_color'].setValue(0xFFF380FF)

        # Calling functions from "Custom writer script"
        write_node['beforeRender'].setValue('custom_writer.run_before()')
        write_node['beforeFrameRender'].setValue('custom_writer.run_before_each_frame()')
        write_node['afterFrameRender'].setValue('custom_writer.run_after_each_frame()')
        write_node['afterRender'].setValue('custom_writer.run_after()')

    nuke.menu('Nodes').addCommand('Image/WriteLocal', 'create_write_local()')

    # === Select all Write nodes (Nuke 12) ===
    def select_all_writes():
        # deselect everything first
        for n in nuke.allNodes():
            n.setSelected(False)
        # select all Write nodes
        for w in nuke.allNodes('Write'):
            w.setSelected(True)

    # Ajoute la commande dans le menu Nuke (avec raccourci Ctrl+Alt+W)
    nuke.menu('Nuke').addCommand('Select/Select all Write nodes', select_all_writes, 'ctrl+alt+w')
    # Si tu preferes SANS raccourci : remplace la ligne ci-dessus par :
    # nuke.menu('Nuke').addCommand('Select/Select all Write nodes', select_all_writes, '')

    print("End loading Nuke Menu as version 12...")

elif nuke.NUKE_VERSION_MAJOR>=13:
    print("Loading Nuke MENU as version 13+ ...")

    # ### -------------------------------------------------------------------------------------------
    # ### ----------------------------------     Nuke 15+      --------------------------------------
    # ### -------------------------------------------------------------------------------------------


    from crypto import crypto_extract
    import auto_compV2.AutoComp as auto_comp_v2
    from nuke_scanner.NukeScanner import NukeScanner
    import nuke_scannerv2.NukeScanner as NukeScannerV2
    from nuke_scanner import select_unconnected_read
    from nuke_scanner import nuke_delete
    from nukescripts import panels
    import importCamFromMetadata
    import cleanexternalreads

    import stamps
    # >>>PrismStart
    if ((not nuke.env["studio"]) or nuke.env["indie"]) and nuke.env.get("gui"):
        if "pcore" in locals():
            nuke.message("Prism is loaded multiple times. This can cause unexpected errors. Please clean this file from all Prism related content:\n\n%s\n\nYou can add a new Prism integration through the Prism Settings dialog" % __file__)
        elif sys.version[0] == "2":
            nuke.message("Prism supports only Python 3 versions of Nuke.\nPython 3 is the default in Nuke 13 and later.")
        else:
            import os
            import sys

            prismRoot = os.getenv("PRISM_ROOT")

            if not prismRoot:
                prismRoot = "C:/ILLOGIC_APP/Prism/2.0.16/app"

            scriptDir = os.path.join(prismRoot, "Scripts")

            if scriptDir not in sys.path:
                sys.path.insert(0, scriptDir)

            import PrismCore

            pcore = PrismCore.PrismCore(app="Nuke")


    # <<<PrismEnd

    # ------ add the following lines to your menu.py file  ------ 

    toolbar = nuke.toolbar("Nodes")
    toolbar.addMenu("VideoCopilot", icon="VideoCopilot.png")
    toolbar.addCommand( "VideoCopilot/OpticalFlares", "nuke.createNode('OpticalFlares')", icon="OpticalFlares.png")


    panels.registerWidgetAsPanel("auto_comp_v2.AutoComp", 'AutoComp V2', 'illogic_studios.autocompV2')
    bloomMenu = nuke.menu("Nodes").addMenu("bloom", icon="bloom.png")
    bloomMenu.addCommand("Delete unused render", "NukeScanner().run()")
    bloomMenu.addCommand("Delete unused render (new)", "NukeScannerV2.NukeScanner().run()")
    bloomMenu.addCommand("Truly Delete unused render", "nuke_delete.run()")
    bloomMenu.addCommand("Select unused read nodes", "select_unconnected_read.run()")
    bloomMenu.addCommand("Extract crypto as mask", "crypto_extract.run()", "Ctrl+Shift+E")
    bloomMenu.addCommand("Clean external reads", "cleanexternalreads.main(debug_mode=True)")
    s=bloomMenu.addMenu("Tools")
    s.addCommand("Anim Buddy", "nuke.createNode(\"AnimVuddy\")") # >>> Add Anim Buddy tool
    s.addCommand("Card Buddy", "nuke.createNode(\"CardBuddy\")") # >>> Add Card Buddy tool
    s.addCommand("DepthBuddy", "nuke.createNode(\"DepthBuddy\")") # >>> Add Depth Buddy tool
    s.addCommand("Flare Market", "nuke.createNode(\"FlareMarket\")") # >>> Add Flare Market tool
    s.addCommand("Mask Buddy", "nuke.createNode(\"MaskBuddy\")") # >>> Add Mask Buddy tool
    s.addCommand("Projection Buddy", "nuke.createNode(\"ProjectionBuddy\")") # >>> Add Projection Buddy tool
    s.addCommand("Reflection Buddy", "nuke.createNode(\"ReflectionBuddy\")") # >>> Add Reflecrion Buddy tool
    s.addCommand("aeRefractor", "nuke.createNode(\"aeRefracTHOR\")",  icon="aeRefracTHOR.png")
    s.addCommand("Import Cam from Metadata", "importCamFromMetadata.main()")
    n=bloomMenu.addMenu("Nodes")
    n.addCommand('expoglow', 'nuke.createNode("expoglow")')
    n.addCommand('exponential glow', "nuke.createNode(\"exponentialGlow\")")

    ### edit folder path here ###
    DVPath = "R:/pipeline/networkInstall/Nuke/nuke15+_configs/gizmos/Deep2VP_v40/asGroup/"

    ### MJTLab - Deep2VP v4.0 ###
    DVPFam = {"general" : ["Deep2VP","DVPToImage","DVPortal","DVPColorCorrect"] , 
            "matte" : ["DVPmatte","DVPattern","DVProjection"] , 
            "lighting" : ["DVPsetLight","DVPscene","DVPrelight","DVPrelightPT","DVPfresnel"] , 
            "shader" : ["DVP_Shader","DVP_ToonShader"]
            }   
    ### hard code. Don't change it ###
    toolbar = nuke.toolbar("Nodes")
    DVP = toolbar.addMenu("Deep2VP", icon="Deep2VP.png")
    for key,value in DVPFam.items() :
        for item in value :
            if key == "general" :
                DVP.addCommand( "{0}".format(item), "nuke.nodePaste(\"{0}{1}.nk\")".format(DVPath,item), icon="{0}.png".format(item) )
            else:
                DVP.addCommand( "{0}/{1}".format(key,item), "nuke.nodePaste(\"{0}{1}/{2}.nk\")".format(DVPath,key,item), icon="{0}.png".format(item) )
    ### end here ###

    # === Select all Write nodes (Nuke 13+) ===
    def select_all_writes():
        # deselect everything first
        for n in nuke.allNodes():
            n.setSelected(False)
        # select all Write nodes
        for w in nuke.allNodes('Write'):
            w.setSelected(True)

    # Ajoute la commande dans le menu Nuke (avec raccourci Ctrl+Alt+W)
    nuke.menu('Nuke').addCommand('Select/Select all Write nodes', select_all_writes, 'ctrl+alt+w')
    # Si tu preferes SANS raccourci : remplace la ligne ci-dessus par :
    # nuke.menu('Nuke').addCommand('Select/Select all Write nodes', select_all_writes, '')

    print("End loading Nuke MENU as version 13+ ...")
    if nuke.NUKE_VERSION_MAJOR<=14:
        print("skip hack ocio")
        custom_config_path = "R:/pipeline/networkInstall/OpenColorIO-Configs/cg-config-v1.0.0_aces-v1.3_ocio-v2.0.ocio"
        os.environ["OCIO"] = custom_config_path
        print("FORCE OCIO IN INIT.PY TO: %s"%(custom_config_path))
        # Set the OCIO config to 'custom' mode
        nuke.root()['OCIO_config'].setValue('custom')
        # Set the path to the custom config
        nuke.root()['customOCIOConfigPath'].setValue(custom_config_path)
        print("End OCIO FIX ...")