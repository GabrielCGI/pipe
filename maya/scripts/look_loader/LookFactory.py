import re
from .LookStandin import LookAsset, LookFur
from common.utils import *


class LookFactory:
    def __init__(self, current_project_dir):
        self.__current_project_dir = current_project_dir

    def generate(self, standin):
        standin_trsf = standin.getParent()
        trsf_name = standin_trsf.name()
        object_name = trsf_name

        # standin name
        standin_file_path = standin.dso.get()
        if standin_file_path is None:
            return
        match = re.match(r"^.*[\\/](abc|abc_fur)[\\/].*?(?:(.+)_mod\.v[0-9]{3}|(\w+)_[0-9]{2}_fur)\.abc$",
                         standin_file_path)
        if match is None:
            return None

        if match.group(1) == "abc_fur":
            standin_name = match.group(3)
            look_obj = LookFur(standin, standin_name, object_name)
        else:
            standin_name = match.group(2)
            look_obj = LookAsset(standin, standin_name, object_name)

        # Retrieve the looks
        look_obj.retrieve_looks(self.__current_project_dir)
        look_obj.retrieve_uvs(self.__current_project_dir)

        if look_obj.is_valid():
            return look_obj

        return None
