import os
import importlib
import logging

from . import loggingsetup
from . import nukelicenseparser

LOG_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "logconfig.json")
LOG_DIRECTORY = os.path.join(os.environ.get("ILL_LOGS_PATH", "R:/logs"), "nuke_license_parser_logs")
loggingsetup.setup_log("nuke_license_parser", LOG_CONFIG_PATH, LOG_DIRECTORY)
logger = logging.getLogger(__name__)

def main():
    importlib.reload(nukelicenseparser)
    logger.info("Start Nuke License Parser")
    return nukelicenseparser.main()


if __name__ == "__main__":
    main()
