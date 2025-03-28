import importlib

from . import primselector


def run():
    importlib.reload(primselector)
    primselector.run()