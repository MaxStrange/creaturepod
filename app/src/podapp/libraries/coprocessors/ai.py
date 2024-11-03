"""
This module provides high-level API functions for the AI
coprocessor.
"""
from typing import Any
from typing import Dict
from typing import List
from ..common import gstreamer_utils

class AICoprocessor:
    """
    The `AICoprocessor` class should be used as a singleton
    for controlling the AI coprocessor in the system.
    """
    def __init__(self, config: Dict[str, Any]) -> None:
        self.source = None
        self.preprocess = None
        self.model = None
        self.postprocess = None
        self.sink = None
        self.pipeline = None

    def shutdown(self):
        """
        Clean shutdown function.
        """
        if self.pipeline is not None:
            self.pipeline.shutdown()
            self.pipeline = None

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
        TODO: Decide on the API for this. Probably want it to be compiled into a
              GStreamer element instead of an arbitrary Python function that we have to wrap
              in an appsink/src.
        """
        pass

    def set_model(model_fpath: str):
        """
        """
        pass

    def set_postprocess_function(self, postproc_fun):
        """
        TODO: Decide on the API for this. Probably want it to be compiled into a
              GStreamer element instead of an arbitrary Python function that we have to wrap
              in an appsink/src.
        """
        pass

    def set_sinks(self, *sink_uris) -> Exception|None:
        """
        Set the sinks for the AI processing pipeline.

        `sink_uris`: (List of `str`) Each argument should be a URI for a sink. Either an RTSP
        sink (e.g., "rtsp://192.168.1.1:5000"), the word "display", or a path to a file to save.
        """
        for uri in sink_uris:
            if not gstreamer_utils.sink_uri_valid(uri):
                return ValueError(f"Invalid sink URI: {uri}")

        self.sink = gstreamer_utils.GStreamerSink(sink_uris)

    def start(self, loop=False):
        """
        Start the pipeline.
        """
        if self.pipeline is None:
            # It is okay for some of these to be None (only source and sink are technically required to be non-None)
            self.pipeline = gstreamer_utils.GStreamerApp("hailo-pipeline", self.source, self.preprocess, self.model, self.postprocess, self.sink)

        self.pipeline.run(repeat_on_end_of_stream=loop)

    def stop(self):
        """
        Stop the pipeline.
        """
        if self.pipeline is not None:
            self.pipeline.shutdown()
            self.pipeline.rewind()
