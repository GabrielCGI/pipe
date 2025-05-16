from . import pcam_facing_ratio_naive
from . import pcam_facing_ratio_np

import time
import importlib
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

def main():
    start = time.monotonic()
    importlib.reload(pcam_facing_ratio_np)
    logger.info('Numpy mode')
    pcam_facing_ratio_np.main()
    time_s = time.monotonic() - start
    logger.info(f"Time taken: {time_s} s")
