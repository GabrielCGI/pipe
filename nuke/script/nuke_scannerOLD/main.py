import importlib
from common import utils

utils.unload_packages(silent=True, package="nuke_scanner")
importlib.import_module("nuke_scanner")
from nuke_scanner.NukeScanner import NukeScanner
NukeScanner().run()