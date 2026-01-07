import importlib

from . import sendranchcopy

import cProfile
import pstats

# PROFILER = cProfile.Profile()

def run(dev=False):
    importlib.reload(sendranchcopy)

    # print("Profiling...")
    # PROFILER.enable()
    sendranchcopy.run(dev)

    # PROFILER.disable()

    # stats = pstats.Stats(PROFILER)
    # stats.strip_dirs().sort_stats("cumtime").dump_stats(r'R:\pipeline\pipe\houdini\scripts\sendranchcopy\profiling\stats.prof')
    # print("Profiling done.")
    # PROFILER.clear()

    
def run_dev(dev=False):
    from . import debug
    importlib.reload(sendranchcopy)
    importlib.reload(debug)
    debug.debug()
    debug.debugpy.breakpoint()
    sendranchcopy.run(dev)

