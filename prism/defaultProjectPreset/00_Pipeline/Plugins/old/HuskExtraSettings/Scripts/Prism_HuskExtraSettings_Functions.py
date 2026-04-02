# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2023 Richard Frangenberg
# Copyright (C) 2023 Prism Software GmbH
#
# Licensed under GNU LGPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.


from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

from pathlib import Path


class Prism_HuskExtraSettings_Functions(object):


    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.data_cached = {}

        self.core.registerCallback("preRender", self.preRender, plugin=self)
        self.core.registerCallback("preSubmit_Deadline", self.preSubmit_Deadline, plugin=self)


    @err_catcher(name=__name__)
    def preRender(self, *args, **kwargs):
        state = kwargs.get("state")
        settings: dict = kwargs.get('settings')
        if state is None or settings is None:
            return
        outputpath = settings.get('outputName')
        if outputpath is None:
            return
        core = state.core
        if core.appPlugin.pluginName != "Houdini":
            return
        node = state.node
        enable_tile = node.parm("useTiles")
        identifier = Path(outputpath).resolve().as_posix()
        data_cached = {}
        if not enable_tile or not enable_tile.eval():
            data_cached['enable_tile'] = '0'
        else:
            data_cached['enable_tile'] = '1'
        tiles_1 = node.parm("tiles1")
        tiles_2 = node.parm("tiles2")
        if tiles_1:
            data_cached['tiles_1'] = str(tiles_1.eval())
        if tiles_2:
            data_cached['tiles_2'] = str(tiles_2.eval())
        data_cached['comment'] = state.getComment()
        self.data_cached[identifier] = data_cached
            
            
    @err_catcher(name=__name__)
    def preSubmit_Deadline(self, origin, Settings, pluginInfos, arguments):
        core = origin.core
        if core.appPlugin.pluginName != "Houdini":
            return
        outputPath = Settings.get('OutputFilename0')
        if outputPath is None:
            return
        identifier = Path(outputPath).resolve().as_posix()
        data_cached = self.data_cached.get(identifier)
        if data_cached is not None:
            enable_tile = data_cached.get('enable_tile', '0')
            comment = data_cached.get("comment", '')
            tiles_1 = data_cached.get('tiles_1', '1')
            tiles_2 = data_cached.get('tiles_2', '1')
        else:
            enable_tile = "0"
            comment = ""
            tiles_1 = '1'
            tiles_2 = '1'
        if len(arguments) < 4:
            return
        huskSettings: str = str(arguments[3])
        if not huskSettings.endswith(".json"):
            return
        content = core.getConfig(configPath=huskSettings)
        content['enable_tile'] = enable_tile 
        content['node_comment'] = comment
        content['tiles_1'] = tiles_1
        content['tiles_2'] = tiles_2
        core.setConfig(data=content, configPath=huskSettings)


    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True
