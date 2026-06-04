import os
import sys


DEBUG_MODE = True
try:
    python_share_dir = os.getenv("ILL_PYTHON_SHARE_PATH", "")
    DEBUGPY_PATH = os.path.join(
        python_share_dir, "python311_debug_pkgs/Lib/site-packages"
    )
    if DEBUGPY_PATH not in sys.path:
        sys.path.insert(0, DEBUGPY_PATH)
    import debugpy # type: ignore
except ImportError as e:
    print(e)
    DEBUG_MODE = False


def debug():
    if not DEBUG_MODE:
        return

    python_exe = os.path.join(python_share_dir, "..", "python", "Python.3.11.9", "python.exe")
    debugpy.configure(python=python_exe)
    try:
        print("Try to listen")
        debugpy.listen(5678)
    except Exception as e:
        print(e)
        return

    print("Waiting for debugger attach")
    debugpy.wait_for_client()
