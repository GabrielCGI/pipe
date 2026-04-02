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

# Complete path to the pretask script !! REPLACE IF MOVED !!
# Not deployed yet, will be moved
PREJOB_PATH = r"R:\pipeline\pipe\deadline\ranch_copy\CopyJopScripts\render_ranch_prejob.py"
POSTJOB_PATH = r"R:\pipeline\pipe\deadline\ranch_copy\CopyJopScripts\delete_ranchjob_postjob.py"

class Prism_RanchExporter_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.core.registerCallback("preSubmit_Deadline" , self.preSubmit_Deadline, plugin=self)

    @err_catcher(name=__name__)
    def preSubmit_Deadline(self, origin, Settings, pluginInfos, arguments):

        print("preSubmit deadline plugin")

        core = origin.core
        # Ensure the job is sent from Houdini
        if core.appPlugin.pluginName != "Houdini" : 
            return 

        # Ensure it's a render job
        if "_render" in Settings["Name"]:   
            # Attach the prejob and postjob script to the job 
            Settings["PreJobScript"] = PREJOB_PATH  
            Settings["PostJobScript"] = POSTJOB_PATH   

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True
