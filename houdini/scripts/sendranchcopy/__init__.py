import importlib

from . import sendranchcopy


def run():
    importlib.reload(sendranchcopy)
    sendranchcopy.run()