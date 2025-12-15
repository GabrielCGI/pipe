import os

import pstats
import cProfile
from datetime import datetime


_PROFILER = cProfile.Profile()
_PROFILER_STATS_DIR = "R:/devmaxime/dev/nuke/nuke_scripts/auto_comp/dump_stats"

def profile_function(func):
    def inner(*args, **kwargs):
        _PROFILER.enable()
        result = func(*args, **kwargs)
        _PROFILER.disable()
        stats = pstats.Stats(_PROFILER)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stats.strip_dirs().sort_stats("cumtime").dump_stats(
            os.path.join(_PROFILER_STATS_DIR, f"stats_{func.__name__}_{timestamp}.prof")
        )
        return result
    return inner