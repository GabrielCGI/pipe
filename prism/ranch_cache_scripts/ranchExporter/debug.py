import os
import sys
import glob

DEBUG_MODE = True
try:
    python_share_dir = os.getenv("ILL_PYTHON_SHARE_PATH", "")
    DEBUGPY_PATH = os.path.join(
        python_share_dir,
        "python311_debug_pkgs/Lib/site-packages"
    )
    if not DEBUGPY_PATH in sys.path:
        sys.path.insert(0, DEBUGPY_PATH)
    import debugpy
except ImportError as e:
    print(e)
    DEBUG_MODE = False


def debug():
    if not DEBUG_MODE:
        return
    hython_pattern = "C:/Program Files/Side Effects Software/Houdini*/bin/hython3*.exe"
    hythons = glob.glob(hython_pattern)
    hythons.sort()

    if hythons:
        debugpy.configure(python=hythons[-1])
    try:
        debugpy.listen(5678)
    except Exception as e:
        print(e)
        return
    
    print("Waiting for debugger attach")
    debugpy.wait_for_client()