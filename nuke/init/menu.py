#
#
#  Copyright (c) 2014, 2015, 2016, 2017 Psyop Media Company, LLC
#  See license.txt
#
#

# coding: utf-8
import sys
import nuke
import os.path


if nuke.NUKE_VERSION_MAJOR==12:
    print("Loading Nuke Menu as version 12...")
    ### -------------------------------------------------------------------------------------------
    ### ----------------------------------     Nuke 12      ---------------------------------------
    ### -------------------------------------------------------------------------------------------

    from nukescripts import panels
    import LayerShuffler
    from auto_comp.AutoComp import AutoComp
    # from auto_compV2.AutoComp import AutoComp 
    import auto_compV2.AutoComp as auto_comp_v2
    from nuke_scanner.NukeScanner import NukeScanner
    from nuke_scanner import select_unconnected_read
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

    print("End loading Nuke Menu as version 12...")


elif nuke.NUKE_VERSION_MAJOR>=15:
    print("Loading Nuke Menu as version 15+ ...")
    # ### -------------------------------------------------------------------------------------------
    # ### ----------------------------------     Nuke 15+      --------------------------------------
    # ### -------------------------------------------------------------------------------------------
    from nukescripts import panels
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
                prismRoot = "C:/ILLOGIC_APP/Prism/2.0.6/app"

            scriptDir = os.path.join(prismRoot, "Scripts")
            if scriptDir not in sys.path:
                sys.path.append(scriptDir)

            import PrismCore

            pcore = PrismCore.PrismCore(app="Nuke")
    # <<<PrismEnd

    # ------ add the following lines to your menu.py file  ------ 
    toolbar = nuke.toolbar("Nodes")
    toolbar.addMenu("VideoCopilot", icon="VideoCopilot.png")
    toolbar.addCommand( "VideoCopilot/OpticalFlares", "nuke.createNode('OpticalFlares')", icon="OpticalFlares.png")

    import auto_compV2.AutoComp as auto_comp_v2
    
    panels.registerWidgetAsPanel("auto_comp_v2.AutoComp", 'AutoComp V2', 'illogic_studios.autocompV2')

    print("End loading Nuke Menu as version 15+ ...")