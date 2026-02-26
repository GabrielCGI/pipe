from importlib import reload



def mainStandalone(*args):
    from . import refUpdater
    reload(refUpdater)
    
    return refUpdater.instanceWorker(*args)



def mainUI(*args):
    from . import UI_referenceUpdater
    reload(UI_referenceUpdater)

    return UI_referenceUpdater.startWithRef(*args)

def loadingScreen(*args):
    from . import UI_loadingScreen
    reload(UI_loadingScreen)

    return UI_loadingScreen.LoadingWindow(*args)