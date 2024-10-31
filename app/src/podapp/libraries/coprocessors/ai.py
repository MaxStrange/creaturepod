"""
This module provides high-level API functions for the AI
coprocessor.
"""
from typing import Any
from typing import Dict
from ..common import gstreamer_utils

class AICoprocessor:
    """
    The `AICoprocessor` class should be used as a singleton
    for controlling the AI coprocessor in the system.
    """
    def __init__(self, config: Dict[str, Any]) -> None:
        pass

    def shutdown(self):
        """
        Clean shutdown function.
        """
        # TODO
        pass

    def set_source(self, source):
        """
        """
        pass

    def set_preprocess_function(self, preproc_fun):
        """
        """
        pass

    def set_model(model_fpath: str):
        """
        """
        pass

    def set_postprocess_function(self, postproc_fun):
        """
        """
        pass

    def set_sink(self, sink):
        """
        """
        pass

    def start(self):
        """
        """
        pass

    def stop(self):
        """
        """
        pass
