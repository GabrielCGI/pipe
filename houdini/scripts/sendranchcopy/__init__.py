import importlib

from . import ranchExporter
from . import sendranchcopy


def run():
    importlib.reload(ranchExporter)
    importlib.reload(sendranchcopy)
    sendranchcopy.run()