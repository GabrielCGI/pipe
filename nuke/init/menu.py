#
#
#  Copyright (c) 2014, 2015, 2016, 2017 Psyop Media Company, LLC
#  See license.txt
#
#

# coding: utf-8

import nuke

from nukescripts import panels
import LayerShuffler
from auto_comp.AutoComp import AutoComp

import cryptomatte_utilities
import MultiChannelCombine
import nukeReadLoader
import noice_aov_print
import DeadlineNukeClient

panels.registerWidgetAsPanel("LayerShuffler.LayerShuffler", "Layer Shuffler", "LayerShufflerPanelId")
panels.registerWidgetAsPanel("AutoComp", 'AutoComp', 'illogic_studios.auto_comp')

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