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

    def set_source(self, source_uri: str) -> Exception|None:
        """
        Set the source of the AI processing pipeline.

        `source_uri`: (`str`) The URI for the source of video. A camera ID like 'cam0' as found
        in the appconfig YAML file will be treated as a Raspberry Pi camera module coming over the
        corresponding (0 or 1) CSI port.
        """
        if not gstreamer_utils.source_uri_valid(source_uri):
            return ValueError(f"Invalid source URI: {source_uri}")

        self.source = gstreamer_utils.GStreamerSource(source_uri)

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
