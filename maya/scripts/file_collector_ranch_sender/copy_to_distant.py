import sys
import os
import time
import importlib
import threading

install_dir = r'R:\pipeline\pipe\maya\scripts\file_collector_ranch_sender'
if not sys.path.__contains__(install_dir):
    sys.path.append(install_dir)

modules = [
    "CollectorCopier"
]

for module in modules:
    importlib.import_module(module)

import CollectorCopier
from CollectorCopier import *

collector_copier = CollectorCopier()
collector_copier.run_copy(sys.argv[1])
