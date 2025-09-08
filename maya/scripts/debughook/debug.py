import os
import sys
import logging


DEBUG_MODE = True
try:
    sys.path.append(r'R:\devmaxime\virtualvens\sanitycheck\Lib\site-packages')
    import debugpy
except:
    DEBUG_MODE = False

logger = logging.getLogger(__name__)
_HAS_LOGGER = False


def setup_logger():
    global _HAS_LOGGER
    try:
        streamHandler = logging.StreamHandler()
        streamHandler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        streamHandler.setFormatter(formatter)
        logger.addHandler(streamHandler)
        logger.setLevel(logging.DEBUG)
        _HAS_LOGGER = True
    except:
        _HAS_LOGGER = False


def debug():
    setup_logger()
    
    if not DEBUG_MODE:
        if _HAS_LOGGER:
            logger.info('Debug mode disabled')
        return

    
    hython = r"C:\ILLOGIC_APP\Prism\2.0.16\app\Python311\Prism.exe"
    debugpy.configure(python=hython)
    try:
        debugpy.listen(5678)
    except Exception as e:
        if _HAS_LOGGER:
            logger.info(e)
        return
    
    if _HAS_LOGGER:
        logger.info("Waiting for debugger attach")
    else:
        print("Waiting for debugger attach")
    debugpy.wait_for_client()