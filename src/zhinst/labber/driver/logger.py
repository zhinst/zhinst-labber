import typing as t
import sys
import logging
from logging.handlers import RotatingFileHandler


def configure_logger(
    logger_: logging.Logger, level: int, filepath: t.Optional[str] = None) -> None:
    """Configure logger.

    Setup formatter
    Log to std out
    Configure rotating file handler to keep logging file size reasonable.

    Args:
        logger_: Logger
        level: Log level
        filepath: Logging filepath
    """
    # Set up logger
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%a, %d %b %Y %H:%M:%S",
    )
    # always log to std out
    std_out_handler = logging.StreamHandler(sys.stdout)
    std_out_handler.setFormatter(formatter)
    logger_.addHandler(std_out_handler)
    # log to path if specified
    if filepath:
        # Maximum of 5 MB log files.
        file_handler = RotatingFileHandler(filepath, maxBytes=int(5e6), backupCount=10)
        file_handler.setFormatter(formatter)
        logger_.addHandler(file_handler)
    logger_.setLevel(level)
