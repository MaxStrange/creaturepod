"""
This module contains all the code for parsing the application's configuration file.
"""
from typing import Any
from typing import Dict
import os
import yaml

DEFAULT_CONFIG_FILE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'appconfig.yaml')

def load_config_file(fpath=DEFAULT_CONFIG_FILE_PATH) -> Dict[str, Any]:
    """
    Load the configuration file and return the entire thing
    as a dict.
    """
    with open(fpath, 'r') as f:
        raw = yaml.load(f, Loader=yaml.BaseLoader)

    return raw
