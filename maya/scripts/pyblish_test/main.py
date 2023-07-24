import os
import sys
import importlib
import pyblish.api
import pyblish_maya
import pyblish_qml
import pyblish_lite

from common import utils
import pyblish_test

# Plugins
pyblish.api.deregister_all_paths()
pyblish.api.register_target("test_target")
plugins = os.path.join(os.path.dirname(pyblish_test.__file__), "plugins")
# os.environ["PYBLISHPLUGINPATH"] = plugins
pyblish.api.register_plugin_path(plugins)

# GUI QML
from pyblish_qml import api as qml_api
qml_api.register_python_executable(r"C:\Program Files\Autodesk\Maya2022\bin\mayapy.exe")
# qml_api.register_pyqt5(r"R:\pipeline\networkInstall\python_lib\PyQt5")
pyblish_qml.settings.WindowTitle="Pyblish Test"
pyblish_qml.settings.HiddenSections = []
pyblish_qml.show()
pyblish_qml.show()

# GUI LITE
# pyblish_lite.settings.WindowTitle="Pyblish Test"
# pyblish_lite.show()

