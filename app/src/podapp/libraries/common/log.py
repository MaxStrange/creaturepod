"""
Module for logging.
"""
from typing import Any
from typing import Dict
import logging

LOGGER_NAME = "CREATUREPOD"
ALLOWED_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")

def debug(msg: str):
    """
    Log at the DEBUG level.
    """
    logging.getLogger(LOGGER_NAME).debug(msg)

def info(msg: str):
    """
    Log at the INFO level.
    """
    logging.getLogger(LOGGER_NAME).info(msg)

def warning(msg: str):
    """
    Log at the WARNING level.
    """
    logging.getLogger(LOGGER_NAME).warning(msg)

def error(msg: str):
    """
    Log at the ERROR level.
    """
    logging.getLogger(LOGGER_NAME).error(msg)

def init(config: Dict[str, Any]):
    """
    Initialize the logging set up.
    """
    raw_log_level = str(config['moduleconfig']['logging']['log-level'])
    log_level = raw_log_level
    if log_level not in ALLOWED_LEVELS:
        # Default to ERROR level
        log_level = "ERROR"
        loglevel_invalid = True
    else:
        loglevel_invalid = False

    # Try to find the log file
    raw_fpath = config['moduleconfig']['logging']['log-file-path']
    fpath = raw_fpath
    try:
        test = open(fpath, 'a')
        test.close()
        log_fpath_invalid = False
    except Exception as e:
        fpath = config['moduleconfig']['logging']['log-file-path-dev']
        log_fpath_invalid = True

    handler = logging.FileHandler(fpath, mode='a', encoding='utf-8')
    handler.setLevel(getattr(logging, log_level))
    handler.setFormatter(logging.Formatter("[%(asctime)s:%(name)s:%(levelname)s]: %(message)s"))
    logging.getLogger(LOGGER_NAME).addHandler(handler)

    # Now log any errors we found in configuring the logger
    if loglevel_invalid:
        warning(f"Configuration file's 'log-level' is invalid. Value given: {raw_log_level}")

    if log_fpath_invalid:
        warning(f"Configuration file's 'log-file-path' is invalid. Value given: {raw_fpath}")

    logging.getLogger(LOGGER_NAME).setLevel(log_level)

def enable_logging_to_console(config: Dict[str, Any]):
    """
    Enable logging to the console. Assumes that 'init' has been called already.
    """
    if config['moduleconfig']['logging']['log-to-console']:
        handler = logging.StreamHandler()
        handler.setLevel(logging.getLogger(LOGGER_NAME).level)
        handler.setFormatter(logging.Formatter("[%(asctime)s:%(name)s:%(levelname)s]: %(message)s"))
        logging.getLogger(LOGGER_NAME).addHandler(handler)
