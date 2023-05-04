import importlib
import sys
from common import utils

utils.unload_packages(silent=True, package="file_collector_ranch_sender")
importlib.import_module("file_collector_ranch_sender")
from file_collector_ranch_sender.CollectorCopier import CollectorCopier
collector_copier = CollectorCopier()
collector_copier.run_copy(sys.argv[1])