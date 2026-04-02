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

import os
import re
import glob

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher
from PrismCore import PrismCore

VERSION_PATTERN = r'v(\d{2,9})'
VERSION_PATTERN_COMPILED = re.compile(VERSION_PATTERN)


class Prism_AutoBakeHDRI_Functions(object):

    def __init__(self, core: PrismCore, plugin):
        self.core = core
        self.plugin = plugin
        self.core.registerCallback("postSaveScene", self.postSaveScene, plugin=self)


    def parseLatestVersion(self, cop_name: str):
        hdri_baked_dir = os.path.expandvars("$HIP/hdri_cop")
        if not os.path.exists(hdri_baked_dir):
            return
        hdri_baked_versions = glob.glob(f"{hdri_baked_dir}/{cop_name}_v*")
        if not len(hdri_baked_dir):
            return
        hdri_baked_versions.sort()
        latest_bake = hdri_baked_versions[-1]
        version_match = VERSION_PATTERN_COMPILED.search(latest_bake)
        if not version_match:
            return
        version_span = version_match.span(1)
        version_string = latest_bake[version_span[0]:version_span[1]]
        return int(version_string)


    def bakeHDRICopNetwork(self):
        import hou
        import nodesearch #type: ignore
        stage = hou.node("/stage")
        type_matcher = nodesearch.NodeType("copnet")
        parm_matcher = nodesearch.Parm("live", "==", 1)
        copnet_live_matcher = nodesearch.Group([type_matcher, parm_matcher])
        copnet_to_bake: list[hou.Cop2Node] = copnet_live_matcher.nodes(stage)
        for copnet in copnet_to_bake:
            version = copnet.parm("version")
            live = copnet.parm("live")
            bake = copnet.parm("execute")
            if version is None or live is None or bake is None:
                continue
            latest_version = self.parseLatestVersion(copnet.name())
            if not latest_version:
                continue
            version.set(latest_version+1)
            bake.pressButton()
            live.set(0)
        try:
            hou.hipFile.save()
            print('Scene saved.')
        except hou.Error as e:
            hou.ui.displayMessage(f"Failed to save file: {str(e)}")
            return


    def postSaveScene(
            self, 
            core, filepath, versionUp,
            comment, publish, details):
        """Callback whenever the scene is saved with prism.

        Args:
            core (PrismCore): Prism core API.
            filepath (str): Saved file location.
            versionUp (bool): Wether or not the version was to be incremented.
            comment (str): Comment.
            publish (bool): Is a global publish, only matter when using local prism location.
            details (dict): Save details.
        """
        if self.core.appPlugin.pluginName != "Houdini":
            return
        self.bakeHDRICopNetwork()


    @err_catcher(name=__name__)
    def isActive(self):
        return True
