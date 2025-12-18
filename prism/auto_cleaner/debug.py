import sys


DEBUG_MODE = True
try:
    sys.path.append('R:/pipeline/networkInstall/python_shares/python37_debug_pkgs/Lib/site-packages')
    import debugpy
except:
    DEBUG_MODE = False


def debug():
    if not DEBUG_MODE:
        return
    
    python_exe = "R:/pipeline/networkInstall/python/Python.3.7.7/python.exe"
    debugpy.configure(python=python_exe)
    try:
        print("Try to listen")
        debugpy.listen(5678)
    except Exception as e:
        print(e)
        return
    
    print("Waiting for debugger attach")
    debugpy.wait_for_client()