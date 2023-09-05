import os
import re
import pymel.core as pm
from abc import ABC, abstractmethod
from enum import Enum
from common.utils import *


class LookPresentState(Enum):
    NotPlugged = 0,
    AnteriorVersionPlugged = 1,
    AlreadyPlugged = 2


class LookStandin(ABC):
    @staticmethod
    def __get_free_operator_slot(standin):
        """
        Get the first free operator slot of the StandIn
        :param standin
        :return: index slot
        """
        index = 0
        while True:
            if pm.getAttr(standin + ".operators[" + str(index) + "]") is None:
                return index
            index += 1

    def __init__(self, standin, standin_name, object_name):
        """
        Constructor
        :param standin
        :param standin_name
        :param object_name
        """
        self.__object_name = object_name
        self._valid = True
        self._standin = standin
        self._standin_name = standin_name
        self._looks = {}
        self._uvs = []

    def get_object_name(self):
        """
        Getter of object name
        :return: object name
        """
        return self.__object_name

    #
    def get_standin_name(self):
        """
        Getter of standin name
        :return: standin name
        """
        return self._standin_name

    # Getter of the standin
    def get_standin(self):
        """
        Getter of the standin
        :return: standin
        """
        return self._standin

    # Getter of the looks
    def get_looks(self):
        """
        Getter of the looks
        :return: looks
        """
        return self._looks

    # Getter of whether the standin object is valid
    def is_valid(self):
        """
        Getter of whether the standin object is valid
        :return: is valid
        """
        return self._valid

    def is_looks_up_to_date(self):
        """
        Getter of whether the looks are up to date
        :return: is looks up to date
        """
        for look_name, look_data in self._looks.items():
            look_state = look_data[1]
            if (look_name in ["default", "override"] and look_state == LookPresentState.NotPlugged) or \
                    look_state == LookPresentState.AnteriorVersionPlugged:
                return False
        return True

    def add_looks(self, filepath_looks, replace_looks):
        """
        Add Looks to the operators
        :param filepath_looks
        :return:
        """
        # print_var(filepath_looks,list(self._looks.items()))
        # return
        for look_filepath in filepath_looks:
            for look_name, look_data in self._looks.items():
                if look_data[0] == look_filepath:
                    to_unplug = []
                    if look_data[1] == LookPresentState.AlreadyPlugged:
                        # If Replace Mode disconnect all the other looks
                        if replace_looks:
                            for ln, ld in self._looks.items():
                                if ld[2] != look_data[2] :
                                    # Unplug all the looks except the current (add to a list to unplug)
                                    to_unplug.append(ld[2])
                    elif look_data[1] == LookPresentState.AnteriorVersionPlugged:
                        include_graph = look_data[2]
                        include_graph.filename.set(look_filepath)
                    else:
                        # If Replace Mode replace the first one
                        if replace_looks and len(self._looks) > 0:
                            replaced = False
                            to_unplug = []
                            for ln, ld in self._looks.items():
                                if ld[1] == LookPresentState.AlreadyPlugged or ld[1] == LookPresentState.AnteriorVersionPlugged :
                                    include_graph = ld[2]
                                    if not replaced:
                                        # Replace the first
                                        include_graph.filename.set(look_filepath)
                                        include_graph.setName("aiIncludeGraph_" +self.__object_name + "_" + look_name)
                                        replaced = True
                                    else:
                                        # Unplug the others looks (add to a list to unplug)
                                        to_unplug.append(include_graph)
                        else:
                            # Create a new look
                            include_graph = pm.createNode("aiIncludeGraph", n="aiIncludeGraph_" +
                                                                              self.__object_name + "_" + look_name)
                            include_graph.filename.set(look_filepath)
                            include_graph.out >> self._standin.operators[
                                LookStandin.__get_free_operator_slot(self._standin)]
                    if replace_looks and len(to_unplug) >0:
                        # Do Unplug
                        index = 0
                        to_unplug_remaining = len(to_unplug)
                        while to_unplug_remaining>0 or index ==20:
                            attribute = self.__object_name + ".operators[" + str(index) + "]"
                            if pm.getAttr(attribute) in to_unplug:
                                pm.disconnectAttr(attribute)
                                to_unplug_remaining-=1
                            index += 1
                        return # Stop after replacing
        pm.select(clear=True)

    #
    def update_existent_looks(self):
        """
        Update existent Looks to the operators
        :return:
        """
        for look_name, look_data in self._looks.items():
            look_filepath = look_data[0]
            look_state = look_data[1]
            if look_name in ["default", "override"] and look_state == LookPresentState.NotPlugged:
                include_graph = pm.createNode("aiIncludeGraph", n="aiIncludeGraph_" + self.__object_name + "_" + look_name)
                include_graph.filename.set(look_filepath)
                include_graph.out >> self._standin.operators[LookStandin.__get_free_operator_slot(self._standin)]
            elif look_state == LookPresentState.AnteriorVersionPlugged:
                include_graph = look_data[2]
                include_graph.filename.set(look_filepath)
        pm.select(clear=True)

    @abstractmethod
    def is_uv_up_to_date(self):
        """
        Getter of whether the uvs are up to date
        :return: is uv up to date
        """
        pass

    @abstractmethod
    def retrieve_uvs(self, current_project_dir):
        """
        Retrieve the UVs
        :param current_project_dir
        :return:
        """
        pass

    @abstractmethod
    def retrieve_looks(self, current_project_dir):
        """
        Retrieve the looks
        :param current_project_dir
        :return:
        """
        pass

    def _retrieve_looks_aux(self, current_project_dir, folder_sublook, suffix_operator, check_for_override=False):
        """
        Auxiliary function to retrieve looks
        :param current_project_dir
        :param folder_sublook
        :param suffix_operator
        :param check_for_override
        :return:
        """
        # Looks
        looks = {}

        # Looks dir
        looks_main_dir = os.path.join(current_project_dir, "assets", self._standin_name, "publish")

        # Find default look
        look_default = ""
        for f in reversed(os.listdir(looks_main_dir)):
            filepath = os.path.join(looks_main_dir, f).replace("\\", "/")
            match = re.match(r"^" + self._standin_name + suffix_operator + r"\.v[0-9]{3}\.ass$", f)
            if os.path.isfile(filepath) and match:
                look_default = filepath
                break
        # If default is not found then stop the function (valid is False)
        if look_default is None:
            self._valid = False
            return

        # Find sublooks within the look folder
        sublooks_dir = os.path.join(looks_main_dir, folder_sublook)
        if os.path.isdir(sublooks_dir):
            for sublook_dir in os.listdir(sublooks_dir):
                sublook_dir_path = os.path.join(sublooks_dir, sublook_dir).replace("\\", "/")
                if not os.path.isdir(sublook_dir_path):
                    continue
                sublooks = []
                for sublook in os.listdir(sublook_dir_path):
                    if re.match(r"^" + self._standin_name + "_" + sublook_dir + suffix_operator + r"\.v[0-9]{3}\.ass$",
                                sublook):
                        sublooks.append(sublook)

                if len(sublooks) == 0:
                    continue
                sublook_path = os.path.join(sublook_dir_path, sublooks[-1]).replace("\\", "/")
                looks[sublook_dir] = [sublook_path, LookPresentState.NotPlugged, None]

        looks = dict(sorted(looks.items()))

        self._looks["default"] = [look_default, LookPresentState.NotPlugged, None]

        if check_for_override:
            # Find the Override Look
            for f in os.listdir(looks_main_dir):
                filepath = os.path.join(looks_main_dir, f).replace("\\", "/")
                match = re.match(r"^" + self._standin_name + suffix_operator + r"\.ass$", f)
                if os.path.isfile(filepath) and match:
                    self._looks["override"] = [filepath, LookPresentState.NotPlugged, None]
                    break

        for look_name, look_data in looks.items():
            self._looks[look_name] = look_data

        # Determine if the look is used, not used or if a precedent version is used
        plugged_looks = {include_graph.filename.get().replace("\\", "/"): include_graph
                         for include_graph in pm.listConnections(self._standin, type="aiIncludeGraph")}
        suffix_operator_or_override = \
            suffix_operator if not check_for_override else "(?:_override|" + suffix_operator + ")"
        for plugged_look_path, plugged_look in plugged_looks.items():
            match = re.match(r"^(.+" + suffix_operator_or_override + r").+$", plugged_look_path)
            if not match: continue
            root_look_path = match.group(1)
            for look_name in self._looks.keys():
                if self._looks[look_name][0] == plugged_look_path:
                    self._looks[look_name][1] = LookPresentState.AlreadyPlugged
                    self._looks[look_name][2] = plugged_look
                elif self._looks[look_name][0].startswith(root_look_path) and \
                        self._looks[look_name][1] != LookPresentState.AlreadyPlugged:
                    self._looks[look_name][1] = LookPresentState.AnteriorVersionPlugged
                    self._looks[look_name][2] = plugged_look


class LookAsset(LookStandin):
    @staticmethod
    def get_uvs(standin_name, current_project_dir):
        """
        Getter of UVs
        :param standin_name
        :param current_project_dir
        :return: uvs
        """
        assets_folder = os.path.join(current_project_dir, "assets")
        uv_folder = os.path.join(assets_folder, standin_name, "abc")
        uvs = []
        if os.path.isdir(uv_folder):
            for file in os.listdir(uv_folder):
                file_path = os.path.join(uv_folder, file)
                print("LOG: %s" % file_path)
                match = re.match(r".*mod(?:\.v([0-9]{3}))?\.abc", file, re.IGNORECASE)
                if os.path.isfile(file_path) and match:
                    try:
                        uvs.append((int(match.group(1)), file_path))
                    except:
                        print("INT MATCH GROUP FAILED")
            uvs = sorted(uvs, reverse=True)
        return uvs

    def retrieve_looks(self, current_project_dir):
        """
        Retrieve the looks
        :param current_project_dir
        :return:
        """
        self._retrieve_looks_aux(current_project_dir, "look", "_operator", True)

    def is_uv_up_to_date(self):
        """
        Getter of whether the uvs are up to date
        :return: is uv up to date
        """
        if len(self._uvs) == 0:
            return True
        dso = self._standin.dso.get()
        match = re.match(r".*mod(?:\.v([0-9]{3}))?\.abc", dso, re.IGNORECASE)
        if not match:
            return False
        return int(match.group(1)) == self._uvs[0][0]

    def retrieve_uvs(self, current_project_dir):
        """
        Retrieve the UVs
        :param current_project_dir
        :return:
        """
        self._uvs = LookAsset.get_uvs(self._standin_name, current_project_dir)
        if len(self._uvs) == 0:
            self._valid = False

    def update_uvs(self):
        """
        Update the UVs
        :return:
        """
        if len(self._uvs) == 0:
            print_warning("No mod files found for " + self.__object_name, char_filler='-')
            return
        self._standin.dso.set(self._uvs[0][1])

class LookFur(LookStandin):
    def retrieve_looks(self, current_project_dir):
        """
        Retrieve the looks
        :param current_project_dir
        :return:
        """
        self._retrieve_looks_aux(current_project_dir, "look_fur", "_fur", False)

    def is_uv_up_to_date(self):
        """
        UVs always up to date with fur
        :return: is uv up to date
        """
        return True

    def retrieve_uvs(self, current_project_dir):
        # Nothing
        pass
