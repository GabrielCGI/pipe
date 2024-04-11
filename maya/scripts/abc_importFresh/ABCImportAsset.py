import os
import re
import traceback
import importlib

from abc import *
from enum import Enum

import pymel.core as pm

from look_loader import LookFactory, LookStandin
importlib.reload(LookFactory)
importlib.reload(LookStandin)
from look_loader.LookFactory import LookFactory
from look_loader.LookStandin import LookAsset

from common.utils import *


class ABCState(Enum):
    """
    ABC State in the scene
    """
    UpToDate = 0
    OutOfDate = 1
    New = 2


class ABCImportAsset(ABC):
    def __init__(self, name, current_project_dir, look_factory, versions=None):
        """
        Constructor
        :param name
        :param current_project_dir
        :param look_factory : Factory of Look (in package look_loader)
        :param versions
        """
        if versions is None:
            versions = []
        self._name = name
        self._current_project_dir = current_project_dir
        self.__versions = sorted(versions, reverse=True)
        self._look_factory = look_factory
        self._import_path = self.__versions[0] if len(self.__versions) > 0 else None
        self._actual_version = None
        self._actual_standins = []
        self._look_standin_obj = None

    def get_icon_filename(self, state):
        """
        Get icon filename according to the state
        :param state
        :return: icon filename
        """
        if state == ABCState.UpToDate:
            return "valid.png"
        elif state == ABCState.OutOfDate:
            return "warning.png"
        else:
            return "new.png"

    def get_name(self):
        """
        Getter of the name
        :return: name
        """
        return self._name

    def _get_char_name(self):
        """
        Getter of the char name
        :return: char name
        """
        return self._name[:-len(self._name.split("_")[-1]) - 1]

    def get_versions(self):
        """
        Getter of the versions
        :return: versions
        """
        return self.__versions

    def set_import_path(self, path):
        """
        Setter of the current import version
        :param path
        :return:
        """
        self._import_path = path

    def get_import_path(self):
        """
        Getter of the current import version
        :return: current import version
        """
        return self._import_path

    def set_actual_version(self, version_path):
        """
        Setter of the actual version
        :param version_path:
        :return:
        """
        self._actual_version = version_path

    def get_actual_version(self):
        """
        Getter of the actual version
        :return: actual version
        """
        return self._actual_version

    def set_actual_standins(self, standins):
        """
        Setter of the actual Standin
        :param standin:
        :return:
        """

        self._actual_standins = standins
        if len(self._actual_standins) > 0:
            try:
                for standin in self._actual_standins:

                    self._look_standin_obj = self._look_factory.generate(standin)
            except Exception as e:
                print_warning("Error while retrieving Looks files of " + self._name, char_filler='-')
                print(f'caught {type(e)}: e')
                print(e)
                traceback.print_exception(*sys.exc_info())

    @abstractmethod
    def import_update_abc(self, do_update_uvs_shaders):
        """
        Import the abc in the scene
        :param do_update_uvs_shaders:
        :return:
        """
        pass

    def update(self):
        """
        Update the shader and uvs of the abc
        :return:
        """
        if self._look_standin_obj is not None:
            self._look_standin_obj.update_existent_looks()

    def is_look_up_to_date(self):
        """
        Getter of whether the abc has his uv and looks up to date
        :return: is look up to date
        """
        if self._look_standin_obj is None:
            return False
        return self._look_standin_obj.is_looks_up_to_date() and self._look_standin_obj.is_uv_up_to_date()

    @staticmethod
    def _configure_standin(standin_node):
        """
        Configure some parameters of the StandIn
        :param standin_node:
        :return:
        """
        current_unit = pm.currentUnit(time=True, query=True)
        unit_to_fps = {
            "game": 15,
            "film": 24,
            "pal": 25,
            "ntsc": 30,
            "show": 48,
            "palf": 50,
            "ntscf": 60,
        }
        if standin_node.name().startswith("frame"): #HACK ZOOTROP SWA 2023
            return
        standin_node.abcFPS.set(unit_to_fps[current_unit] if current_unit in unit_to_fps else 24)
        standin_node.useFrameExtension.set(True)


class ABCImportAnim(ABCImportAsset):
    def import_update_abc(self, do_update_uvs_shaders):
        """
        Import or Update an animation
        :param do_update_uvs_shaders
        :return:
        """
        is_import = len(self._actual_standins) == 0

        char_name = self._get_char_name()
        last_uv = None


        name = self.get_name()

        # If import we create the standin
        if is_import:
            actual_standin = pm.createNode("aiStandIn", n=name+"Shape")
            standin_node = pm.listRelatives(actual_standin, parent=True)[0]
            standin_node = pm.rename(standin_node, name)
            actual_standins = [actual_standin]
            standin_nodes = [standin_node]
        else:
            actual_standins = self._actual_standins
            standin_nodes = []
            for standin in actual_standins:
                standin_nodes.append(pm.listRelatives(standin, parent=True)[0])
        print(actual_standins)

        abc_filename = name + ".abc"
        abc_filepath = os.path.join(self._import_path, abc_filename)
        for standin_node in standin_nodes:
            standin_node.mode.set(6)
            standin_node.dso.set(abc_filepath)
            ABCImportAsset._configure_standin(standin_node)

        self.set_actual_standins(actual_standins)
        
        light_filename = name + "_light.ma"
        light_filepath = os.path.join(self._import_path, light_filename)

        # Update anim lights or create one
        if os.path.exists(light_filepath):
            found = False
            for ref in pm.listReferences():
                match = re.match(r".*[\\/]" + name + r"_light\.m[ab]", ref.unresolvedPath())
                if match:
                    ref.replaceWith(light_filepath)
                    found = True
                    break
            if not found:
                pm.createReference(light_filepath, defaultNamespace=True)

        if is_import or do_update_uvs_shaders:
            self.update()
        return standin_nodes


class ABCImportFur(ABCImportAsset):

    def get_icon_filename(self, state):
        """
        Get fur icon filename according to the state
        :param state
        :return: icon filename
        """
        if state == ABCState.UpToDate:
            return "valid_fur.png"
        elif state == ABCState.OutOfDate:
            return "warning_fur.png"
        else:
            return "new_fur.png"

    def get_name(self):
        """
        Get the fur name
        :return:
        """
        return self._name + "_fur"

    def import_update_abc(self, do_update_uvs_shaders):
        """
        Import or Update a fur
        :param do_update_uvs_shaders
        :return:
        """
        is_import = len(self._actual_standins) == 0

        name = self.get_name()
        dso = None
        standin_node = None

        for f in os.listdir(self._import_path):
            if re.match(r"" + name + r"(?:\.[0-9]+)?\.abc", f):
                dso = f
                break

        if dso is not None:
            # If import we create the standin
            if is_import:
                actual_standin = pm.createNode("aiStandIn", n="shape_" + name)
                standin_node = pm.listRelatives(actual_standin, parent=True)[0]
                standin_node = pm.rename(standin_node, name)
                actual_standins = [actual_standin]
                standin_nodes = [standin_node]
            else:
                actual_standins = self._actual_standins
                standin_nodes = []
                for standin in actual_standins:
                    standin_nodes.append(pm.listRelatives(standin, parent=True)[0])


            self.set_actual_standins(actual_standins)
            for standin_node in standin_nodes:
                standin_node.dso.set(os.path.join(self._import_path, dso))
                standin_node.mode.set(4)
                ABCImportAsset._configure_standin(standin_node)

            if is_import or do_update_uvs_shaders:
                self.update()
        return standin_nodes
