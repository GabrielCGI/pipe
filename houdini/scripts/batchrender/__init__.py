
from . import batchrender
from . import farmsubmitter
import importlib


def main():
    importlib.reload(batchrender)
    importlib.reload(farmsubmitter)
    batchrender.main()
    

def debug():
    import houdiniutils
    importlib.reload(houdiniutils)
    houdiniutils.debug()
    houdiniutils.breakpoint()
    main()