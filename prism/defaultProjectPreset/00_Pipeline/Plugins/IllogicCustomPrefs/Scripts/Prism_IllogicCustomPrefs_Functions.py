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


import copy

from PrismUtils.Decorators import err_catcher_plugin as err_catcher


class Prism_IllogicCustomPrefs_Functions(object):
    PREFS = {
        "globals": {
            "mediaPlayerName": "RV",
            "mediaPlayerPath": r"C:\ILLOGIC_APP\OpenRV\bin\rv.exe",
        },
        "dccoverrides": {
            "Houdini_override": True,
            "Houdini_path": "launcher:Houdini",
            "Maya_override": True,
            "Maya_path": "launcher:Maya",
        },
        "usd": {
            "openViewport": False,
        },
        "browser": {
            "showAssetSearch": True,
        },
    }

    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.set_prism_prefs()
        self.core.registerCallback("postInitialize", self.set_prism_prefs, plugin=self)
        # self.core.registerCallback("onUserSettingsOpen", self.on_user_settings_open, plugin=self)
        # self.core.registerCallback("userSettings_saveSettings", self.on_user_settings_save, plugin=self)

    @err_catcher(name=__name__)
    def isActive(self):
        return True

    @err_catcher(name=__name__)
    def set_prism_prefs(self, *args, **kwargs):
        if self.core.getConfig() is None:
            return
        
        self.core.setConfig(data=copy.deepcopy(self.PREFS), configPath=self.core.userini)
