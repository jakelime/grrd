import logging
import os
import time
import platform

from logging.handlers import RotatingFileHandler
from pathlib import Path


APP_NAME = "gaia"


class ConfigError(ValueError):
    """Raised when there are errors in the configuration file"""


def get_time(datetimestrformat: str = "%Y%m%d_%H%M%S"):
    """
    Returns the datetime string at the time of function call
    :param datetimestrformat: datetime string format, defaults to "%Y%m%d_%H%M%S"
    :type datetimestrformat: str, optional
    :return: datetime in string format
    :rtype: str
    """
    return time.strftime(datetimestrformat, time.localtime(time.time()))


def setup_logger(name: str = "", default_level: str = "INFO", log_fp_str: str = ""):
    """Set up logger

    :param default_level: logging level, defaults to "INFO"
    :type default_level: str, optional
    :param log_fp_str: filepath to store the logfile, defaults to ""
    :type log_fp_str: str, optional
    :return: logger instance
    :rtype: logging.Logger
    """
    if not name:
        logger = logging.getLogger(__name__)
    else:
        logger = logging.getLogger(name)

    if not logger.hasHandlers():
        # return logger
        time_str_format = "%y-%j %H:%M"
        if log_fp_str:
            log_filepath = Path(os.path.expanduser(log_fp_str))
        else:
            log_filepath = Path(os.path.expanduser("~")) / "tmp" / f"{APP_NAME}.log"

        if not log_filepath.is_file():
            log_filepath.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(log_filepath, maxBytes=5_242_880, backupCount=10)
        file_handler.setFormatter(
            logging.Formatter(
                "%(levelname)-8s: [%(asctime)s]: %(message)s", time_str_format
            )
        )
        file_handler.setLevel(default_level)
        logger.addHandler(file_handler)

        if not platform.system() == "Linux":
            # Creates a streamhandler if we are running on MacOS or Win
            # This is for engineering, viewing output streams
            s_handler = logging.StreamHandler()
            s_handler.setLevel(default_level)
            s_handler.setFormatter(logging.Formatter("%(levelname)-8s: %(message)s"))
            logger.addHandler(s_handler)

        logger.setLevel(default_level)
        logger.info(f"logger initialized. time string formatter -> {time_str_format}")
        logger.info(f"{log_filepath=}")

    return logger


if __name__ == "__main__":
    log = setup_logger(APP_NAME)
    pass
