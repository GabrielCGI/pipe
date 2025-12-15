import os
import shutil
import cProfile
import pstats

PROFILER = cProfile.Profile()

def benchNTime(func, count, *args, **kwargs):
    for i in range(count):
        PROFILER.enable()
        func(*args, **kwargs)
        PROFILER.disable()

def move_twice(src, dst):
    shutil.move(src, dst)
    shutil.move(dst, src)
    
def rename_twice(src, dst):
    os.rename(src, dst)
    os.rename(dst, src)

if __name__ == '__main__':
    src_move = "R:/pipeline/pipe/prism/auto_cleaner/v010"
    dst_move = "R:/pipeline/pipe/prism/auto_cleaner/old/v010"

    benchNTime(move_twice, 1000, src_move, dst_move)

    stats = pstats.Stats(PROFILER)
    stats.strip_dirs().sort_stats("cumtime").print_stats(20)
    PROFILER.clear()

    # src_rename = "R:/pipeline/pipe/prism/auto_cleaner/v001"
    # dst_rename = "R:/pipeline/pipe/prism/auto_cleaner/_OLD_v001"
    
    # benchNTime(rename_twice, 1000, src_rename, dst_rename)

    # stats = pstats.Stats(PROFILER)
    # stats.strip_dirs().sort_stats("cumtime").print_stats(20)
    # PROFILER.clear()