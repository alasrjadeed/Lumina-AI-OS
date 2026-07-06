import logging
import sys


def setup_log(name: str = "kernel") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        "%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(handler)
    return logger


log = setup_log()
