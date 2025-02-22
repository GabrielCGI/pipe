import time
try:
    from alive_progress import alive_bar
    ALIVE_BAR_IMPORTED = True
except:
    ALIVE_BAR_IMPORTED = False

SHOW_TIME = True
LOG = False
FULL_TIME_NS_ELAPSED = 0

def timeElapsed(func):
    def inner(*args, **kwargs):
        
        if not SHOW_TIME:
            return func(*args, **kwargs)
        
        start = time.process_time_ns()
        result = func(*args, **kwargs)
        time_ns = time.process_time_ns() - start
        time_sec = time_ns / 1000000000
        
        print(f"Function: {func.__name__}")
        print(f"as taken: {time_sec} s | {time_ns} ns")
        return result
    return inner

def fullTimeElapsed(func):
    def inner(*args, **kwargs):
        global FULL_TIME_NS_ELAPSED
        
        if not SHOW_TIME:
            return func(*args, **kwargs)
        
        start = time.process_time_ns()
        result = func(*args, **kwargs)
        time_ns = time.process_time_ns() - start
        FULL_TIME_NS_ELAPSED += time_ns
        
        return result
    return inner

def doNtimeFunc(func, n, *args, **kwargs):
    if ALIVE_BAR_IMPORTED:
        with alive_bar(n) as bar:
            for i in range(n):
                func(*args, **kwargs)
                bar()
    else:
        for i in range(n):
            func(*args, **kwargs)

def printFullTime():
    time_sec = FULL_TIME_NS_ELAPSED / 1000000000
    print(f"Time taken: {time_sec} s | {FULL_TIME_NS_ELAPSED} ns")

def printAvgTime(n):
    time_sec = FULL_TIME_NS_ELAPSED / 1000000000
    if n <= 0:
        avg_sec = 0.0
        avg_ns = 0
    else:
        avg_sec = time_sec/n
        avg_ns = FULL_TIME_NS_ELAPSED/n
    print(f"Average time per call: {avg_sec} s "
          f"| {avg_ns} ns")