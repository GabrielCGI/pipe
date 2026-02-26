from importlib import reload



def mainUI(*args):
    from .UI import UI_referenceUpdater
    reload(UI_referenceUpdater)
    return UI_referenceUpdater.MainUI(*args)

def noUI(*args):
    from .Core import RU_core
    reload(RU_core)
    return RU_core.RefUpdaterCore(*args)