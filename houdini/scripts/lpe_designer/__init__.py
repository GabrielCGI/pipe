from . import lpe_designer
import importlib

def createInterface(reload=False):
    if reload:
        importlib.reload(lpe_designer)
    return lpe_designer.LPEDesigner()