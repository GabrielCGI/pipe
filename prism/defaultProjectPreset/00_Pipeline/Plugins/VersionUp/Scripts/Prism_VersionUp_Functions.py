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

import os
import shutil

class Prism_VersionUp_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin

        self.core.registerCallback("openPBListContextMenu", self.mediaContextMenuRequested, plugin=self)

    @err_catcher(name=__name__)
    def mediaContextMenuRequested(self, mediaBrowser, menu, lw, item, path):
        
        if not item:
            return

        if lw.objectName() == "tw_identifier":
            if item.childCount() >= 1:
                return
        
        self.add_versionup_action(menu, path)

    def add_versionup_action(self, menu, path):
        act_vup = menu.addAction("Version Up")
        act_vup.triggered.connect(lambda: self.version_up(path))

    def version_up(self, path):        
        files_to_copy =  self.get_all_files(path)
        current_version = os.path.basename(path)
        next_version = self.get_next_version(path)

        for file in files_to_copy:
            self.copy_and_rename(file, current_version, next_version)

    def get_all_files(self, root):

        to_copy = []
        for path, subdirs, files in os.walk(root):
            for name in files:
                file = os.path.join(path, name)
                to_copy.append(file)

        return to_copy

    def get_next_version(self, path):
        parent_dir = os.path.abspath(os.path.join(path, os.pardir))
        versions = [f for f in os.listdir(parent_dir) if f.startswith('v') and f[1:].isdigit()]
        versions.sort()
        latest_version = int(versions[-1][1:])
        next_version = f"v{latest_version + 1:03d}"
        return next_version

    def copy_and_rename(self, file_path, current_version, next_version):

        new_file = file_path.replace(current_version, next_version)
        new_dir = os.path.dirname(new_file)
        
        os.makedirs(new_dir, exist_ok=True)
        
        shutil.copy(file_path, new_file)
        print(new_file)

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True
