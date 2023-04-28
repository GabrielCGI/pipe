import os
import re
import pymel.core as pm
from enum import Enum
from common.utils import *

class LookPresentState(Enum):
    NotPlugged = 0,
    AnteriorVersionPlugged = 1,
    AlreadyPlugged = 2

class LookStandin:
    @staticmethod
    def __get_free_operator_slot(standin):
        index = 0
        while True:
            if pm.getAttr(standin + ".operators[" + str(index) + "]") is None:
                return index
            index += 1

    def __init__(self, standin):
        self.__standin = standin
        self.__standin_name = ""
        standin_trsf = standin.getParent()
        trsf_name = standin_trsf.name()
        self.__object_name = trsf_name
        self.__valid = False
        self.__looks = {}

        # standin name
        standin_file_path = standin.dso.get()
        print_var(standin_file_path)
        if standin_file_path is None or not re.match(r".*\.abc", standin_file_path):
            return
        standin_file_name_ext = os.path.basename(standin_file_path)
        standin_file_name = os.path.splitext(standin_file_name_ext)[0]
        self.__standin_name = re.sub("_" + standin_file_name.split('_')[-1], '', standin_file_name)

        # Retrieve the looks
        self.__valid = self.retrieve_looks()

    def retrieve_looks(self):
        # Looks
        looks = {}
        dso = self.__standin.dso.get()
        match = re.match(r"^(.*)[\\\/]abc[\\\/].*$", dso)
        if not match:
            return False

        looks_main_dir = os.path.join(match.group(1), "publish")

        # Find default look
        look_default = ""
        for f in reversed(os.listdir(looks_main_dir)):
            filepath = os.path.join(looks_main_dir, f).replace("\\", "/")
            match = re.match(r"^" + self.__standin_name + r"_operator\.v[0-9]{3}\.ass$", f)
            if os.path.isfile(filepath) and match:
                look_default = filepath
                break
        # If default is not found then stop the function (valid is False)
        if look_default is None:
            return False

        # Find sublooks within the look folder
        sublooks_dir = os.path.join(looks_main_dir, "look")
        if os.path.isdir(sublooks_dir):
            for sublook_dir in os.listdir(sublooks_dir):
                sublook_dir_path = os.path.join(sublooks_dir, sublook_dir).replace("\\", "/")
                if not os.path.isdir(sublook_dir_path):
                    continue
                sublooks = os.listdir(sublook_dir_path)
                if len(sublooks) == 0:
                    continue
                sublook_path = os.path.join(sublook_dir_path, sublooks[-1]).replace("\\", "/")
                looks[sublook_dir] = [sublook_path, LookPresentState.NotPlugged, None]

        looks = dict(sorted(looks.items()))

        self.__looks["default"] = [look_default, LookPresentState.NotPlugged, None]

        # Find the Override Look
        for f in os.listdir(looks_main_dir):
            filepath = os.path.join(looks_main_dir, f).replace("\\", "/")
            match = re.match(r"^" + self.__standin_name + r"_override\.ass$", f)
            if os.path.isfile(filepath) and match:
                self.__looks["override"] = [filepath, LookPresentState.NotPlugged, None]
                break

        for look_name, look_data in looks.items():
            self.__looks[look_name] = look_data

        plugged_looks = {include_graph.filename.get().replace("\\", "/") : include_graph
                         for include_graph in pm.listConnections(self.__standin, type="aiIncludeGraph")}
        for plugged_look_path, plugged_look in plugged_looks.items():
            match = re.match(r"^(.+)(?:_override|_operator).+$", plugged_look_path)
            if not match:continue
            root_look_path = match.group(1)
            for look_name in self.__looks.keys():
                if self.__looks[look_name][0] == plugged_look_path:
                    self.__looks[look_name][1] = LookPresentState.AlreadyPlugged
                elif self.__looks[look_name][0].startswith(root_look_path) and \
                        self.__looks[look_name][1] != LookPresentState.AlreadyPlugged:
                    self.__looks[look_name][1] = LookPresentState.AnteriorVersionPlugged
                    self.__looks[look_name][2] = plugged_look
        return True

    # Getter of object name
    def get_object_name(self):
        return self.__object_name

    # Getter of standin name
    def get_standin_name(self):
        return self.__standin_name

    # Getter ofthe  standin
    def get_standin(self):
        return self.__standin

    # Getter of the looks
    def get_looks(self):
        return self.__looks

    # Getter of whether the standin object is valid
    def is_valid(self):
        return self.__valid

    # Add Looks to the operators
    def add_looks(self, filepath_looks):
        for look_filepath in filepath_looks:
            for look_name, look_data in self.__looks.items():
                if look_data[0] == look_filepath:
                    if look_data[1] == LookPresentState.AlreadyPlugged:
                        continue
                    elif look_data[1] == LookPresentState.AnteriorVersionPlugged:
                        include_graph = look_data[2]
                    else:
                        include_graph = pm.createNode("aiIncludeGraph", n="aiIncludeGraph_" + look_name)
                    include_graph.filename.set(look_filepath)
                    include_graph.out >> self.__standin.operators[LookStandin.__get_free_operator_slot(self.__standin)]
        pm.select(clear=True)
