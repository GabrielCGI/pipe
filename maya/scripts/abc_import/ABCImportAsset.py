import os
import re
from abc import *
from enum import Enum

from pymel.core import *

from utils import *


# ABC State in the scene
class ABCState(Enum):
    UpToDate = 0
    OutOfDate = 1
    New = 2


class ABCImportAsset(ABC):
    def __init__(self, name, current_project_dir, versions=None):
        if versions is None:
            versions = []
        self._name = name
        self.__versions = sorted(versions, reverse=True)
        self._current_project_dir = current_project_dir
        self._import_path = self.__versions[0] if len(self.__versions) > 0 else None
        self._actual_version = None
        self._actual_standin = None

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

    # Import the abc in the scene
    @abstractmethod
    def import_update_abc(self, do_update_uvs_shaders):
        pass

    # Update the shader and uvs of the abc
    @abstractmethod
    def update(self):
        pass

    # Getter of whether the abc has his uvs and shaders up to date
    @abstractmethod
    def is_up_to_date(self):
        pass

    @staticmethod
    def _configure_standin(standin_node):
        current_unit = currentUnit(time=True, query=True)
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
    # Getter of the mod files of the anim
    def __get_mod_files(self):
        abc_char_name = self._name[:-len(self._name.split("_")[-1]) - 1]
        assets_folder = os.path.join(self._current_project_dir, "assets")
        mod_folder = assets_folder + "\\" + abc_char_name + "\\abc\\"
        mod_files = []
        if os.path.isdir(mod_folder):
            for file in os.listdir(mod_folder):
                file_path = os.path.join(mod_folder, file)
                if os.path.isfile(file_path) and re.match(r".*mod(?:\.v[0-9]+)?\.abc", file, re.IGNORECASE):
                    mod_files.append(file_path)
            mod_files = sorted(mod_files, reverse=True)
        return mod_files

    # Getter of whether the abc has his uvs up to date
    def __is_mod_up_to_date(self):
        # Test if mod is up to date
        mod_files = self.__get_mod_files()
        standin_node = listRelatives(self._actual_standin, parent=True)[0]
        actual_mod_path = standin_node.dso.get()
        if len(mod_files) == 0 or actual_mod_path is None:
            return False
        mod_regexp = r".*mod\.v([0-9]+)\.abc"
        mod_match = re.match(mod_regexp, mod_files[0])
        mod_match_actual = re.match(mod_regexp, actual_mod_path)
        if mod_match and mod_match_actual:
            last_version_num = int(mod_match.group(1))
            actual_version_num = int(mod_match_actual.group(1))
            if last_version_num > actual_version_num:
                return False
        return True

    # Update uvs
    def __update_mod(self):
        # MOD (UV)
        try:
            mod_files = self.__get_mod_files()
            mod_file_path = mod_files[0]
            standin_node = listRelatives(self._actual_standin, parent=True)[0]
            standin_node.dso.set(mod_file_path)
        except:
            print_warning("No mod files found for " + self.get_name(), char_filler='-')

    # Getter of the operator files of the anim
    def __get_operator_files(self):
        abc_char_name = self._name[:-len(self._name.split("_")[-1]) - 1]
        assets_folder = os.path.join(self._current_project_dir, "assets")
        operator_folder = assets_folder + "\\" + abc_char_name + "\\publish"
        operator_files = []
        if os.path.isdir(operator_folder):
            for file in os.listdir(operator_folder):
                file_path = os.path.join(operator_folder, file)
                if os.path.isfile(file_path) and re.match(r".*operator(?:\.v[0-9]+)?\.ass", file, re.IGNORECASE):
                    operator_files.append(file_path)
            operator_files = sorted(operator_files, reverse=True)
        return operator_files

    # Getter of whether the abc has his shaders up to date
    def __is_operator_up_to_date(self):
        # Test if operator is up to date
        operator_files = self.__get_operator_files()
        if len(operator_files) == 0:
            return False
        include_graphs = listConnections(self._actual_standin, type="aiIncludeGraph")
        if len(include_graphs) == 0:
            return False
        set_shader = include_graphs[0]
        actual_operator_path = set_shader.filename.get()
        operator_regexp = r".*operator\.v([0-9]+)\.ass"
        operator_match = re.match(operator_regexp, operator_files[0])
        operator_match_actual = re.match(operator_regexp, actual_operator_path)
        if operator_match and operator_match_actual:
            last_version_num = int(operator_match.group(1))
            actual_version_num = int(operator_match_actual.group(1))
            if last_version_num > actual_version_num:
                return False
        return True

    # Update shader
    def __update_operator(self):
        standin_node = listRelatives(self._actual_standin, parent=True)[0]

        name = self.get_name()
        # OPERATOR (SHADER)
        try:
            operator_files = self.__get_operator_files()
            operator_file_path = operator_files[0]
        except:
            print_warning("No operator files found for " + name, char_filler='-')
            return standin_node

        include_graphs = listConnections(self._actual_standin, type="aiIncludeGraph")
        # If include graph exists we retrieve it instead of creating one
        if len(include_graphs) > 0:
            set_shader = include_graphs[0]
        else:
            set_shader = createNode("aiIncludeGraph", n="aiIncludeGraph_" + name)
        set_shader.filename.set(operator_file_path)
        set_shader.out >> standin_node.operators[0]
        return standin_node

    def import_update_abc(self, do_update_uvs_shaders):
        is_import = self._actual_standin is None

        name = self.get_name()
        # If import we create the standin
        if is_import:
            self._actual_standin = createNode("aiStandIn", n="shape_" + name)
            standin_node = listRelatives(self._actual_standin, parent=True)[0]
            standin_node = rename(standin_node, name)
        else:
            standin_node = listRelatives(self._actual_standin, parent=True)[0]

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
            for ref in listReferences():
                match = re.match(r".*[\\/]" + name + "_light\.m[ab]", ref.unresolvedPath())
                if match:
                    ref.replaceWith(light_filepath)
                    found = True
                    break
            if not found:
                createReference(light_filepath, defaultNamespace=True)

        if is_import or do_update_uvs_shaders:
            self.update()
        return standin_node

    def is_up_to_date(self):
        # Test if mod is up-to-date
        mod_up_to_date = self.__is_mod_up_to_date()
        if not mod_up_to_date: return False
        # Test if operator is up-to-date
        operator_up_to_date = self.__is_operator_up_to_date()
        if not operator_up_to_date: return False
        return True

    def update(self):
        self.__update_mod()
        return self.__update_operator()


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

    # Getter of the operator files of the fur
    def __get_operator_files(self):
        abc_char_name = self._name[:-len(self._name.split("_")[-1]) - 1]
        assets_folder = os.path.join(self._current_project_dir, "assets")
        operator_folder = assets_folder + "\\" + abc_char_name + "\\publish"
        operator_files = []
        if os.path.isdir(operator_folder):
            for file in os.listdir(operator_folder):
                file_path = os.path.join(operator_folder, file)
                if os.path.isfile(file_path) and re.match(r".*fur(?:\.v[0-9]+)?\.ass", file, re.IGNORECASE):
                    operator_files.append(file_path)
            operator_files = sorted(operator_files, reverse=True)
        return operator_files

    # Getter of whether the fur has his shaders up to date
    def __is_operator_up_to_date(self):
        # Test if operator is up to date
        operator_files = self.__get_operator_files()
        if len(operator_files) == 0:
            return False
        include_graphs = listConnections(self._actual_standin, type="aiIncludeGraph")
        if len(include_graphs) == 0:
            return False
        set_shader = include_graphs[0]
        actual_operator_path = set_shader.filename.get()
        operator_regexp = r".*fur\.v([0-9]+)\.ass"
        operator_match = re.match(operator_regexp, operator_files[0])
        operator_match_actual = re.match(operator_regexp, actual_operator_path)
        if operator_match and operator_match_actual:
            last_version_num = int(operator_match.group(1))
            actual_version_num = int(operator_match_actual.group(1))
            if last_version_num > actual_version_num:
                return False
        return True

    # Update shaders
    def __update_operator(self):
        standin_node = listRelatives(self._actual_standin, parent=True)[0]

        name = self.get_name()
        # OPERATOR (SHADER)
        try:
            operator_files = self.__get_operator_files()
            operator_file_path = operator_files[0]
        except:
            print_warning("No operator files found for " + name, char_filler='-')
            return standin_node
        include_graphs = listConnections(self._actual_standin, type="aiIncludeGraph")
        # If include graph exists we retrieve it instead of creating one
        if len(include_graphs) > 0:
            set_shader = include_graphs[0]
        else:
            set_shader = createNode("aiIncludeGraph", n="aiIncludeGraph_" + name)
        set_shader.filename.set(operator_file_path)
        set_shader.out >> standin_node.operators[0]
        return standin_node

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
                self._actual_standin = createNode("aiStandIn", n="shape_" + name)
                standin_node = listRelatives(self._actual_standin, parent=True)[0]
                standin_node = rename(standin_node, name)
            else:
                standin_node = listRelatives(self._actual_standin, parent=True)[0]

            standin_node.dso.set(os.path.join(self._import_path, dso))
            standin_node.mode.set(4)
            ABCImportAsset._configure_standin(standin_node)

            if is_import or do_update_uvs_shaders:
                self.update()
        return standin_node

    def update(self):
        return self.__update_operator()

    def is_up_to_date(self):
        # Test if operator is up to date
        return self.__is_operator_up_to_date()
