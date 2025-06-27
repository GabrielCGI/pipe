import importlib

from . import sendranchcopy


def run(dev=False):
    importlib.reload(sendranchcopy)
    sendranchcopy.run(dev)
    
    
def run_dev(dev=False):
    from . import debug
    importlib.reload(sendranchcopy)
    importlib.reload(debug)
    debug.debug()
    debug.debugpy.breakpoint()
    sendranchcopy.run(dev)