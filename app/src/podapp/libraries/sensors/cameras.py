"""
This module provides high-level API functions
for the cameras in the system.
"""
from typing import Any
from typing import Dict
from ..common import log
from ..outputs import gpio
from ..gstreamer_utils import app as gst_app
from ..gstreamer_utils import source as gst_source
from ..gstreamer_utils import sink as gst_sink

# TODO: This whole module is going to need to be reconsidered when I get around to dealing with the camera mux

class Camera:
    """
    The `Camera` class provides high-level functionality for a camera hardware module.
    """
    def __init__(self, config: Dict[str, Any], config_name: str) -> None:
        self.pipeline = None

        self.cam_id = str(config['pinconfig']['cameras'][config_name]['id'])
        self.cam_mux = int(config['pinconfig']['cameras']['camera-mux']['pin'])
        level = str(config['pinconfig']['cameras'][config_name]['mux-active-level'])
        self.mux_level = gpio.Level.HIGH if level == 'HIGH' else gpio.Level.LOW
        self.enabled = config['pinconfig']['cameras'][config_name]['enabled'].lower() == "true"

        if self.enabled:
            # Set up the camera mux pin
            gpio.configure_pin(self.cam_mux, gpio.Direction.OUT)

    def _switch_to_this_camera(self):
        """
        Switch to this camera.
        """
        if self.enabled:
            gpio.output(self.cam_mux, self.mux_level)

    def shutdown(self) -> None:
        """
        Clean shutdown function.
        """
        if self.enabled:
            self.stop_streaming()
            gpio.deconfigure_pin(self.cam_mux)

    def stream_to_display(self) -> Exception|None:
        """
        Asynchronously stream to the display.
        """
        if self.enabled:
            self._switch_to_this_camera()

            source = gst_source.GStreamerSource(self.cam_id)
            sink = gst_sink.GStreamerSink("display")
            self.pipeline = gst_app.GStreamerApp("camera-to-display", source, sink)
            self.pipeline.run()

        return None

    def stream_to_file(self, fpath: str) -> Exception|None:
        """
        Asynchronously stream to a file.
        """
        if self.enabled:
            self._switch_to_this_camera()

            source = gst_source.GStreamerSource(self.cam_id)
            sink = gst_sink.GStreamerSink(fpath)
            self.pipeline = gst_app.GStreamerApp("camera-to-file", source, sink)
            self.pipeline.run()

        return None

    def stop_streaming(self) -> Exception|None:
        """
        Stop streaming.
        """
        if self.enabled:
            self._switch_to_this_camera()

            if self.pipeline is not None:
                self.pipeline.shutdown()
                self.pipeline = None

        return None

class FrontCamera(Camera):
    """
    The `FrontCamera` singleton class.
    """
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config, 'front-camera')

class RearCamera(Camera):
    """
    The `RearCamera` singleton class.
    """
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config, 'rear-camera')
