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


class Prism_IllogicCustomPrefs_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.set_prism_prefs()

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True

    def set_prism_prefs(self):
        import json
        import os
        # import socket
        # if socket.gethostname() == "FOX-04":
        #     import sys
        #     DEBUG_MODULE = "R:/devmaxime/dev/python/debug"
        #     if not DEBUG_MODULE in sys.path:
        #         sys.path.insert(0, DEBUG_MODULE)
        #     import debug
        #     debug.debug()
        #     debug.debugpy.breakpoint()
        # try:
        # Récupère le chemin du dossier "Mes documents" de l'utilisateur actuel
        user_documents = os.path.join(os.path.expanduser('~'), 'Documents', 'Prism2')
        json_file_path = os.path.join(user_documents, 'Prism.json')
        self.core.configs.cachedConfigs.pop(json_file_path, None)

        # Charge le fichier JSON existant
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except Exception:
            return

        # Modifie les valeurs spécifiques
        # DCC Overrides options
        if (data.get('dccoverrides') is None
            or data.get('usd') is None
            or data.get('globals') is None):
            return
        
        data['dccoverrides']['Houdini_path'] = 'launcher:Houdini'
        data['dccoverrides']['Maya_path'] = 'launcher:Maya'
        data['dccoverrides']['Houdini_override'] = True
        data['dccoverrides']['Maya_override'] = True
        # USD options
        data['usd']['openViewport'] = False
        # asset search
        data['showAssetSearch'] = True
        # Media player
        data['globals']['mediaPlayerName'] = "RV"
        data['globals']['mediaPlayerPath'] = "C:\\ILLOGIC_APP\\OpenRV\\bin\\rv.exe"
        print ("Prism Illogic Custom Prefs done working")


        # Sauvegarde les modifications dans le fichier JSON
        with open(json_file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)
        # except:
        #     pass
        #print("Les valeurs ont été modifiées avec succès.")
