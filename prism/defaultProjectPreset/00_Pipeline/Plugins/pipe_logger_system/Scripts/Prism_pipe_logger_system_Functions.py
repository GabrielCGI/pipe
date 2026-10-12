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

import datetime
import logging.config
import logging
import socket
import json
import glob
import sys
import os


from PrismUtils.Decorators import err_catcher_plugin as err_catcher #type: ignore



LOG_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "configs", "logconfig.json")



class Prism_pipe_logger_system_Functions(object):
    def __init__(self, core, plugin):
        self.plugin = plugin
        self.core = core

        self._createLogger(core.projectPath.replace("\\", "/").split("/")[-2], self.core.appPlugin.pluginName)
        logger = logging.getLogger("IllogicPlugin.pipe_logger_system")
        logger.info("plugin pipe_logger_system load and ready to USE")
    
    
    def _createLogger(self, prod: str, dcc: str) -> None:
        log_directory = f"R:/logs/plugin_prod_log/{prod}/{dcc}"

        self._cleanLog(log_directory, 5, True)
        self._setupLog("pluginIllogic", log_directory)

    def _cleanLog(self, path_logs: str, max_log: int, by_machine: bool) -> None:
        machine = "*"
        if max_log <= 0:
            max_log = 1
        if by_machine:
            machine = socket.gethostname()

        to_search = f"{path_logs}/log_{machine}_pluginIllogic_*.log"
        allp = sorted(glob.glob(to_search), reverse=True)
        if not allp:
            return
        
        to_del = allp[max_log-1:]
        for path in to_del:
            try:
                os.remove(path)
            except Exception:
                pass

    def _setupLog(self, logName: str, logDirectory: str) -> None:
        log_config = None
        with open(LOG_CONFIG_PATH, "r") as log_file:
            log_config = json.load(log_file)
        if not log_config:
            print("No config", file=sys.stderr)
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        machine = socket.gethostname()

        log_name = f"log_{machine}_{logName}_{timestamp}.log"
        log_file = os.path.join(logDirectory, log_name)
        os.makedirs(logDirectory, exist_ok=True)

        log_config["handlers"]["file"]["filename"] = log_file
        logging.config.dictConfig(log_config)
