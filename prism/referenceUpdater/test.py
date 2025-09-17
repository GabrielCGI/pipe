import maya.standalone
import ctypes
import time
import sys



maya.standalone.initialize(name='python')
ctypes.windll.kernel32.AllocConsole()
sys.stdout = open('CONOUT$', 'w')
sys.stdin = open('CONIN$', 'r')

def tt(msg):
    try:
        print(msg, file=sys.stdout)
    except:
        pass


tt("test_out")
print("test error", file=sys.stderr)
time.sleep(1)

tt("test_out")
print("test error", file=sys.stderr)
time.sleep(1)

tt("test_out")
print("test error", file=sys.stderr)
time.sleep(1)

tt("test_out")
print("test error", file=sys.stderr)
time.sleep(1)

maya.standalone.uninitialize()
