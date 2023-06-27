import json
import base64
import os.path

import pymel.core as pm
from common.utils import *
from .Preset import *


class PresetManager:
    # ################################################### Singleton ####################################################
    __instance = None

    @staticmethod
    def get_instance():
        """
        Getter of the instance for the Singleton pattern
        :return: instance of PresetManager
        """
        if PresetManager.__instance is None:
            PresetManager.__instance = PresetManager()
            PresetManager.__instance.retrieve_presets()
            PresetManager.__instance.retrieve_default_presets()
        return PresetManager.__instance

    # ################################################### Singleton ####################################################

    def __init__(self):
        self.__presets = []
        self.__default_presets = []
        self.__active_preset = None

    def clear(self):
        """
        Clear the presets
        :return:
        """
        self.__presets.clear()
        self.__active_preset = None

    def add_preset(self, preset_to_add):
        """
        Add a preset
        :param preset_to_add
        :return:
        """
        to_remove = None
        for preset in self.__presets:
            if preset.get_name() == preset_to_add.get_name():
                to_remove = preset
                break
        if to_remove is not None:
            self.remove_preset(to_remove)
        if preset_to_add.is_active():
            for curr_preset in self.__presets:
                curr_preset.set_active(False)

        if preset_to_add not in self.__presets:
            self.__presets.append(preset_to_add)

    def remove_preset(self, preset_to_remove):
        """
        Remove a preset
        :param preset_to_remove
        :return:
        """
        if preset_to_remove is not None:
            self.__presets.remove(preset_to_remove)

    def set_preset_active(self, active_preset):
        """
        Setter of the active state of a preset
        :param active_preset
        :return:
        """
        # Set all presets to inactive except the wanted one
        if active_preset is not None:
            for preset in self.__presets:
                preset.set_active(preset is active_preset)

    def retrieve_presets(self):
        """
        Retrieve the existing presets in the scene
        :return:
        """
        self.clear()
        if "presets" in pm.fileInfo:
            found_active = False
            json_presets = pm.fileInfo["presets"].replace("\\\"", "\"")
            try:
                arr_json_presets = json.loads(json_presets)
                for json_preset in arr_json_presets:
                    preset = Preset.create_from_existant(json_preset)
                    if preset.is_active() and not found_active:
                        self.__active_preset = preset
                    self.__presets.append(preset)
            except:
                print_warning("Error while trying to parse an existing preset")

    def save_presets(self):
        """
        Save presets in the scene
        :return:
        """
        arr_json_presets = []
        for preset in self.__presets:
            arr_json_presets.append(preset.to_preset_array())
        pm.fileInfo["presets"] = json.dumps(arr_json_presets)

    def get_presets(self):
        """
        Getter of the presets
        :return: presets
        """
        self.__presets.sort(key=lambda x: x.get_name())
        return self.__presets

    def get_default_presets(self):
        """
        Getter of the default presets
        :return: default presets
        """
        return self.__default_presets

    def retrieve_default_presets(self):
        """
        Retrieve all the default presets
        :return:
        """
        self.__default_presets = []
        default_preset_dir = os.path.join(os.path.dirname(__file__), "default_preset")
        for preset_filename in os.listdir(default_preset_dir):
            preset_path = os.path.join(default_preset_dir, preset_filename)
            try:
                if os.path.isfile(preset_path):
                    with open(preset_path, "r") as f:
                        preset_json = f.read().replace("\\\"", "\"").replace("\\n", "")
                        self.__default_presets.append(Preset.create_from_existant(json.loads(preset_json)))
            except:
                print_warning("Error while trying to parse a default preset : "+preset_path)

    def has_preset_with_name(self, name):
        """
        Getter of whether a preset exist with a given name
        :param name
        :return: has preset with name
        """
        for preset in self.__presets:
            if preset.get_name() == name:
                return True
        return False
