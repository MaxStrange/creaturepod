"""
Utilities for the tests.
"""
import subprocess
from typing import Any
from typing import Dict
from ..src.podapp.libraries.common import appconfig
from ..src.podapp.libraries.common import log

def in_wsl_mode() -> bool:
    """
    Return whether we are running in WSL (and therefore cannot access certain features).
    """
    p = subprocess.run("uname -r".split(), capture_output=True, encoding="utf-8")
    p.check_returncode()
    return "microsoft" in p.stdout.lower()

def initialize_logger(config: Dict[str, Any]):
    """
    Initialize the logger.
    """
    log.init(config)

def load_config() -> Dict[str, Any]:
    """
    Load the configuration file.
    """
    return appconfig.load_config_file()
