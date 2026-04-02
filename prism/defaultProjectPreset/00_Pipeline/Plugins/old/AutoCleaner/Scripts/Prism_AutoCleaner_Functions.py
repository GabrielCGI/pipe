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

import sys

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

import PrismCore
from PrismUtils.Decorators import err_catcher_plugin as err_catcher

AUTO_CLEANER_PATH = "R:/pipeline/pipe/prism"
if not AUTO_CLEANER_PATH in sys.path:
    sys.path.insert(0, AUTO_CLEANER_PATH)

import auto_cleaner
from auto_cleaner.entitytype import EntityType # type: ignore

class Prism_AutoCleaner_Functions(object):
    def __init__(self, core: PrismCore.PrismCore, plugin):
        self.core = core
        self.plugin = plugin
        
        self.core.registerCallback("postRender", self.postRender, plugin=self)
        self.core.registerCallback("postExport", self.postExport, plugin=self)
        self.core.registerCallback("postSaveScene", self.postSaveScene, plugin=self)


    def postRender(self, *args, **kwargs):
        if self.core.appPlugin.pluginName == "Nuke":
            scene_path = kwargs["scenefile"]
            reads_path = auto_cleaner.getReadPathToVersion()
            auto_cleaner.clean(
                scene_path=scene_path,
                entity_type=EntityType._2D_RENDER,
                print_only=False
            )
            auto_cleaner.clean(
                scene_path=scene_path,
                entity_type=EntityType._3D_RENDER,
                exclude_list=reads_path,
                print_only=False
            )

    
    def postExport(self, *args, **kwargs):
        scene_path = kwargs["scenefile"]
        auto_cleaner.clean(
            scene_path=scene_path,
            entity_type=EntityType._PRODUCT,
            print_only=False
        )
        
    
    def postSaveScene(self, *args, **kwargs):
        scene_path = args[1]
        auto_cleaner.clean(
            scene_path=scene_path,
            entity_type=EntityType._SCENEFILE,
            print_only=False
        )

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True
