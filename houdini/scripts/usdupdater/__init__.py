import importlib


def checkEveryNodes():
    from . import updater
    importlib.reload(updater)
    updater.checkEveryNodes()