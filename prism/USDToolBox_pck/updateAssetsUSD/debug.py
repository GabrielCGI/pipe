import os
import sys
import logging


_PYTHON_EXEC = os.environ.get("UD_DEBUG_PYTHON_EXEC")
_DEBUGPY_PATH = os.environ.get("UD_DEBUGPY_PATH")

if _DEBUGPY_PATH is not None:
    if not _DEBUGPY_PATH in sys.path:
        sys.path.append(_DEBUGPY_PATH)


def create_logger(log_file):
    logger = logging.getLogger(__name__)
    
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    if log_file is not None:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        fileHandler = logging.FileHandler(log_file)
        fileHandler.setLevel(logging.DEBUG) 
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)

    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(logging.INFO)
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

    logger.setLevel(logging.DEBUG)
    return logger


def debug(port=5678, log_file=None):
    logger: logging.Logger = create_logger(log_file)

    try:
        import debugpy
    except ImportError as e:
        logger.warning(e)
        return
    
    if _PYTHON_EXEC is not None:
        debugpy.configure(python=_PYTHON_EXEC)
    try:
        debugpy.listen(port)
    except Exception as e:
        logger.info(e)
        return
    
    logger.info("Waiting for debugger attach")
    debugpy.wait_for_client()
