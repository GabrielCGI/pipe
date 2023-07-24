#
#
#  Copyright (c) 2014, 2015, 2016, 2017 Psyop Media Company, LLC
#  See license.txt
#
#


from nukescripts import panels
import LayerShuffler
from auto_comp.AutoComp import AutoComp

panels.registerWidgetAsPanel("LayerShuffler.LayerShuffler", "Layer Shuffler", "LayerShufflerPanelId")
panels.registerWidgetAsPanel("AutoComp", 'AutoComp', 'illogic_studios.auto_comp')


import cryptomatte_utilities
import MultiChannelCombine
import nukeReadLoader
import noice_aov_print


cryptomatte_utilities.setup_cryptomatte_ui()
collectMenu = nuke.menu("Nodes").addMenu("Collect_Files")
collectMenu.addCommand('Collect Files', 'collectFiles.collectFiles()')
collectMenu.addCommand('Help', 'collectFiles.myBlog()')

bloomMenu = nuke.menu("Nodes").addMenu("bloom","bloom.png")
bloomMenu.addCommand("Multi Channel Combine", "MultiChannelCombine.MultiChannelCombine()")
bloomMenu.addCommand("Reads update", "nukeReadLoader.start()")
bloomMenu.addCommand("Denoise AOVs List", "noice_aov_print.run()")

toolbar = nuke.toolbar("Nodes")
toolbar.addMenu("VideoCopilot", icon="VideoCopilot.png")
toolbar.addCommand( "VideoCopilot/OpticalFlares", "nuke.createNode('OpticalFlares')", icon="OpticalFlares.png")


import DeadlineNukeClient
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
import nuke

# if ((not nuke.env["studio"]) or nuke.env["indie"]) and nuke.env.get("gui"):
#     if "pcore" in locals():
#         nuke.message("Prism is loaded multiple times. This can cause unexpected errors. Please clean this file from all Prism related content:\n\n%s\n\nYou can add a new Prism integration through the Prism Settings dialog" % __file__)
#     else:
#         import os
#         import sys
#
#         prismRoot = os.getenv("PRISM_ROOT")
#         if not prismRoot:
#             prismRoot = "C:/Program Files/Prism2"
#
#         scriptDir = os.path.join(prismRoot, "Scripts")
#         if scriptDir not in sys.path:
#             sys.path.append(scriptDir)
#
#         import PrismCore
#
#         pcore = PrismCore.PrismCore(app="Nuke")
# <<<PrismEnd
