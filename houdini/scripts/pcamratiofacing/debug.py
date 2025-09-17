import sys

DEBUG_MODE = True
DEBUG_MODULE_PATH = "R:/pipeline/networkInstall/python_shares/python311_debug_pkgs/Lib/site-packages"
try:
    if not DEBUG_MODULE_PATH in sys.path:
        sys.path.insert(0, DEBUG_MODULE_PATH)
    import debugpy
except:
    DEBUG_MODE = False


def debug(houdini_version=613):
    if not DEBUG_MODE:
        return
    
    hython = f"C:/PROGRA~1/SIDEEF~1/HOUDIN~1.{houdini_version}/bin/hython3.11.exe"
    debugpy.configure(python=hython)
    try:
        debugpy.listen(5678)
    except Exception as e:
        print(e)
        return
    
    print("Waiting for debugger attach")
    debugpy.wait_for_client()