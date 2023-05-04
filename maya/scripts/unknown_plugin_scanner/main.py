import importlib
from common import utils

utils.unload_packages(silent=True, package="unknown_plugin_scanner")
importlib.import_module("unknown_plugin_scanner")

from unknown_plugin_scanner.UnknownPluginScanner import UnknownPluginScanner
try:
    unknown_plugin_scanner.close()
except:
    pass
unknown_plugin_scanner = UnknownPluginScanner()
unknown_plugin_scanner.show()
