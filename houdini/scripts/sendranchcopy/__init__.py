import importlib

from . import sendranchcopy


def run():
    importlib.reload(sendranchcopy)
    sendranchcopy.run()
    
    
def run_dev():
    from . import debug
    importlib.reload(sendranchcopy)
    importlib.reload(debug)
    debug.debug()
    debug.debugpy.breakpoint()
    sendranchcopy.run()