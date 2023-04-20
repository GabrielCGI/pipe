import sys
import re
import json
import importlib
install_dir = r'R:\pipeline\pipe\houdini\scripts\fur_export'
if not sys.path.__contains__(install_dir): sys.path.append(install_dir)
utils_dir = r'R:\pipeline\pipe\maya\scripts\common'
if not sys.path.__contains__(utils_dir): sys.path.append(utils_dir)
modules = ["utils","fur_export"]
from utils import *
unload_packages(silent=True, packages=modules)
for module in modules: importlib.import_module(module)
import fur_export

# ######################################################################################################################

__CURRENT_PROJECT_DIR = r"I:\battlestar_2206"


__OPTIONS = {
    "fps": 25,
    "probability": 0.65,
    "motion_blur": True,
    "samples": 3,
    "shutter": (-0.15, 0.15)
}

__CHAR_DICT_PATH = r'R:\pipeline\pipe\houdini\scripts\fur_export\char_dict.json'

__LOG_FILE_FOLDER = r'R:\pipeline\pipe\houdini\scripts\fur_export\log'

# ######################################################################################################################

with open(__CHAR_DICT_PATH, "r") as char_dict_file:
    char_dict = json.loads(char_dict_file.read())
fur_export.run(__CURRENT_PROJECT_DIR, char_dict, __OPTIONS, __LOG_FILE_FOLDER)
