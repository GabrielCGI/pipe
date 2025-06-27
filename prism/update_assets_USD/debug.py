import os
import sys
import logging


DEBUG_MODE = True
try:
    sys.path.append(r'R:\devmaxime\virtualvens\sanitycheck\Lib\site-packages')
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
    
    hython = r"C:\ILLOGIC_APP\Prism\2.0.16\app\Python311\Prism.exe"
    debugpy.configure(python=hython)
    try:
        debugpy.listen(5678)
    except Exception as e:
        logger.info(e)
        return
    
    logger.info("Waiting for debugger attach")
    debugpy.wait_for_client()