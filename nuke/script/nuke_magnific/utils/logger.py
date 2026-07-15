"""Logging configuration for Magnific upscaler."""

import logging
import logging.handlers
from pathlib import Path
from ..config import LOG_FILE, LOG_DIR


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logger with file and console handlers.

    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # File handler (rotating, max 5MB per file, keep 3 files)
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to setup file logging: {e}")

    # Console handler (only for warnings and errors)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger
