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
from pathlib import Path
import sys

from PrismUtils.Decorators import err_catcher_plugin as err_catcher
from PrismCore import PrismCore


class Prism_pipe_plugins_loader_Functions(object):
    def __init__(self, core: PrismCore, plugin):
        self.core: PrismCore = core
        self.plugin = plugin

        self.core.registerCallback(
            "onProjectChanged", self.on_project_changed, plugin=self
        )

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True

    @err_catcher(name=__name__)
    def on_project_changed(self, *args, **kwargs):
        prism_job = os.getenv("PRISM_JOB")
        if not prism_job:
            prism_job = Path(self.core.projectPath).as_posix()
            os.environ["PRISM_JOB"] = prism_job
        general_script_directory = (
            Path(prism_job) / ".pipelines_deploy" / "general" / "scripts"
        )
        if (
            general_script_directory.exists()
            and general_script_directory.as_posix() not in sys.path
        ):
            sys.path.insert(0, general_script_directory.as_posix())
        general_script_beta_directory = (
            Path(prism_job) / ".pipelines_deploy" / "general" / "scripts_beta"
        )
        if (
            general_script_beta_directory.exists()
            and general_script_beta_directory.as_posix() not in sys.path
            and os.getenv("ILL_BETA_MODE")
        ):
            sys.path.insert(0, general_script_beta_directory.as_posix())
        plugin_base_directory = (
            Path(prism_job) / ".pipelines_deploy" / "prism" / "plugins"
        )
        if not plugin_base_directory.exists():
            return
        plugins_dir = [
            p
            for p in plugin_base_directory.iterdir()
            if p.is_dir() and not p.name.endswith("dist-info")
        ]
        self.core.plugins.loadPlugins(pluginPaths=plugins_dir)
