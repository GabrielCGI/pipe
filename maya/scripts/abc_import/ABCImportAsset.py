import os
import re
import traceback
from abc import *
from enum import Enum

import pymel.core as pm

from look_loader.LookFactory import LookFactory
from look_loader.LookStandin import LookAsset
from common.utils import *


# ABC State in the scene
class ABCState(Enum):
    UpToDate = 0
    OutOfDate = 1
    New = 2


class ABCImportAsset(ABC):
    def __init__(self, name, current_project_dir, look_factory, versions=None):
        if versions is None:
            versions = []
        self._name = name
        self._current_project_dir = current_project_dir
        self.__versions = sorted(versions, reverse=True)
        self._look_factory = look_factory
        self._import_path = self.__versions[0] if len(self.__versions) > 0 else None
        self._actual_version = None
        self._actual_standin = None
        self._look_standin_obj = None

    # Get icon filename according to the state
    def get_icon_filename(self, state):
        if state == ABCState.UpToDate:
            return "valid.png"
        elif state == ABCState.OutOfDate:
            return "warning.png"
        else:
            return "new.png"

    # Getter of the name
    def get_name(self):
        return self._name

    # Getter of the name
    def _get_char_name(self):
        return self._name[:-len(self._name.split("_")[-1]) - 1]

    # Getter of the versions
    def get_versions(self):
        return self.__versions

    # Setter of the current import version
    def set_import_path(self, path):
        self._import_path = path

    # Getter of the current import version
    def get_import_path(self):
        return self._import_path

    # Setter of the actual version
    def set_actual_version(self, version_path):
        self._actual_version = version_path

    # Getter of the actual version
    def get_actual_version(self):
        return self._actual_version

    # Setter of the actual Standin
    def set_actual_standin(self, standin):
        self._actual_standin = standin
        if self._actual_standin is not None:
            try:
                self._look_standin_obj = self._look_factory.generate(self._actual_standin)
            except Exception as e:
                print_warning("Error while retrieving Looks files of " + self._name, char_filler='-')
                print(f'caught {type(e)}: e')
                print(e)
                traceback.print_exception(*sys.exc_info())
                return

    # Import the abc in the scene
    @abstractmethod
    def import_update_abc(self, do_update_uvs_shaders):
        pass

    # Update the shader and uvs of the abc
    def update(self):
        if self._look_standin_obj is not None:
            self._look_standin_obj.update_existent_looks()

    # Getter of whether the abc has his uv and looks up to date
    def is_look_up_to_date(self):
        if self._look_standin_obj is None:
            return False
        return self._look_standin_obj.is_looks_up_to_date() and self._look_standin_obj.is_uv_up_to_date()

    @staticmethod
    def _configure_standin(standin_node):
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
        standin_node.abcFPS.set(unit_to_fps[current_unit] if current_unit in unit_to_fps else 24)
        standin_node.useFrameExtension.set(True)


class ABCImportAnim(ABCImportAsset):
    def import_update_abc(self, do_update_uvs_shaders):
        is_import = self._actual_standin is None

        char_name = self._get_char_name()
        try:
            last_uv = LookAsset.get_uvs(char_name, self._current_project_dir)[0][1]
        except Exception as e:
            print(f'caught {type(e)}: e')
            print(e)
            traceback.print_exception(*sys.exc_info())
            print_warning("Error while retrieving UV files of "+char_name, char_filler='-')
            return

        name = self.get_name()

        # If import we create the standin
        if is_import:
            actual_standin = pm.createNode("aiStandIn", n="shape_" + name)
            standin_node = pm.listRelatives(actual_standin, parent=True)[0]
            standin_node = pm.rename(standin_node, name)
        else:
            actual_standin = self._actual_standin
            standin_node = pm.listRelatives(actual_standin, parent=True)[0]

        if is_import or do_update_uvs_shaders:
            actual_standin.dso.set(last_uv)
        self.set_actual_standin(actual_standin)
        abc_filename = name + ".abc"
        abc_filepath = os.path.join(self._import_path, abc_filename)
        standin_node.mode.set(6)
        standin_node.abc_layers.set(abc_filepath)
        ABCImportAsset._configure_standin(standin_node)

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
        return standin_node


class ABCImportFur(ABCImportAsset):

    def get_icon_filename(self, state):
        if state == ABCState.UpToDate:
            return "valid_fur.png"
        elif state == ABCState.OutOfDate:
            return "warning_fur.png"
        else:
            return "new_fur.png"

    def get_name(self):
        return self._name + "_fur"

    def import_update_abc(self, do_update_uvs_shaders):
        is_import = self._actual_standin is None

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
            else:
                actual_standin = self._actual_standin
                standin_node = pm.listRelatives(actual_standin, parent=True)[0]

            standin_node.dso.set(os.path.join(self._import_path, dso))

            self.set_actual_standin(actual_standin)
            standin_node.mode.set(4)
            ABCImportAsset._configure_standin(standin_node)

            if is_import or do_update_uvs_shaders:
                self.update()
        return standin_node
