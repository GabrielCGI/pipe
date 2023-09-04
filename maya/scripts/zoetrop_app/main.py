import importlib
from common import utils
utils.unload_packages(silent=True, package="zoetrop_dev")
importlib.import_module("zoetrop_dev")

from zoetrop_dev.ui import CustomUI

try:
    zoetrop_ui.close()
except:
    pass
zoetrop_ui = CustomUI()
zoetrop_ui.show()
