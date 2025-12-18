import os
import sys
import logging


DEBUG_MODE = True
try:
    PYTHON_SHARE = os.getenv("ILL_PYTHON_SHARE_PATH", "R:/pipeline/networkInstall/python_shares")
    DEBUGPY_PATH = os.path.join(PYTHON_SHARE, "python311_debug_pkgs/Lib/site-packages")
    if not DEBUGPY_PATH in sys.path:
        sys.path.insert(0, DEBUGPY_PATH)
    import debugpy
except:
    DEBUG_MODE = False


def debug():
    logger = logging.getLogger(__name__)
    fileHandler = logging.FileHandler(os.path.join('R:/logs/update_usd_logs', f"log_update_usd.log"))
    fileHandler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)
    logger.setLevel(logging.DEBUG)
    if not DEBUG_MODE:
        return
    
    python_executable = "C:/ILLOGIC_APP/Prism/2.0.18/app/Python311/Prism.exe"
    debugpy.configure(python=python_executable)
    try:
        debugpy.listen(5678)
    except Exception as e:
        logger.info(e)
        return
    
    logger.info("Waiting for debugger attach")
    debugpy.wait_for_client()