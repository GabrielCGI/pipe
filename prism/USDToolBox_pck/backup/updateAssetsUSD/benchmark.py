import os

import cProfile
import pstats

_USD_UPDATER_DIR = os.path.dirname(os.path.dirname(__file__))
_DEFAULT_PROFILE_FILE = os.path.join(_USD_UPDATER_DIR, "stats.prof")

class Profiler():
    
    def __init__(self):
        self.profiler = cProfile.Profile()


    def clear(self):
        self.profiler.clear()


    def profile_function(self, func):
        def inner(*args, **kwargs):
            self.profiler.enable()
            result = func(*args, **kwargs)
            self.profiler.disable()
            return result
        return inner


    def print(self, stats="cumtime"):
        stats = pstats.Stats(self.profiler)
        stats.strip_dirs().sort_stats("cumtime").print_stats(20)


    def dumps_file(self, filename=_DEFAULT_PROFILE_FILE):
        stats = pstats.Stats(self.profiler)
        stats.strip_dirs().sort_stats("cumtime").dump_stats(filename)
