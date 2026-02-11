import os
import sys
import logging


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
    
    python_pattern = "C:/ILLOGIC_APP/Prism/*/app/Python311/Prism.exe"
    pythons = glob.glob(python_pattern)
    pythons.sort()
    if pythons:
        debugpy.configure(python=pythons[-1])
    try:
        debugpy.listen(5678)
    except Exception as e:
        logger.info(e)
        return
    
    logger.info("Waiting for debugger attach")
    debugpy.wait_for_client()