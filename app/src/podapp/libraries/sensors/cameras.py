"""
This module provides high-level API functions
for the cameras in the system.
"""
from typing import Any
from typing import Dict
from ..common import error
from ..common import gstreamer_utils
from ..common import log
from ..outputs import gpio

try:
    from picamera2.encoders import H264Encoder
    from picamera2 import Picamera2
    PICAMERA_ENABLED = True
except ImportError:
    # Can't use picamera. Use GStreamer.
    PICAMERA_ENABLED = False

# TODO: This whole module is going to need to be reconsidered when I get around to dealing with the camera mux

class Camera:
    """
    The `Camera` class provides high-level functionality for a camera hardware module.
    """
    def __init__(self, config: Dict[str, Any], config_name: str) -> None:
        cam_id = str(config['pinconfig']['cameras'][config_name]['id'])

        self.cam_mux = int(config['pinconfig']['cameras']['camera-mux']['pin'])

        level = str(config['pinconfig']['cameras'][config_name]['mux-active-level'])
        self.mux_level = gpio.Level.HIGH if level == 'HIGH' else gpio.Level.LOW

        # Set up the camera mux pin
        gpio.configure_pin(self.cam_mux, gpio.Direction.OUT)

        if not PICAMERA_ENABLED:
            self.model = None
            self.location = None
            self.rotation = None
            self.cam_id = cam_id
            self.camera = None
        else:
            # Collect camera info
            gpio.output(self.cam_mux, gpio.Level.LOW)
            attached_cameras_info0 = Picamera2.global_camera_info()
            gpio.output(self.cam_mux, gpio.Level.HIGH)
            attached_cameras_info1 = Picamera2.global_camera_info()

            # Double check
            attached_cameras_info = [attached_cameras_info0, attached_cameras_info1]
            found = False
            for i, cam in enumerate(attached_cameras_info):
                if cam['Id'] == cam_id:
                    self.model = cam['Model']
                    self.location = cam['Location']
                    self.rotation = cam['Rotation']
                    self.cam_id = cam_id
                    self.camera = Picamera2(i)
                    found = True
                    break

            # Cannot use this camera.
            if not found:
                self.model = None
                self.location = None
                self.rotation = None
                self.cam_id = None
                self.camera = None
                log.warning(f"Cannot find camera with ID {cam_id}")

    def _switch_to_this_camera(self):
        """
        Switch to this camera.
        """
        gpio.output(self.cam_mux, self.mux_level)

    def shutdown(self) -> None:
        """
        Clean shutdown function.
        """
        self.stop_streaming()
        gpio.cleanup(self.cam_mux)

    def stream_to_file(self, fpath: str) -> Exception|None:
        """
        Asynchronously stream to a file.
        """
        self._switch_to_this_camera()

        if PICAMERA_ENABLED:
            video_config = self.camera.create_video_configuration()
            self.camera.configure(video_config)
            encoder = H264Encoder(bitrate=10000000)
            self.camera.start_recording(encoder, fpath)
        else:
            source = gstreamer_utils.GStreamerSource(self.cam_id)
            sink = gstreamer_utils.GStreamerSink(fpath)
            self.pipeline = gstreamer_utils.GStreamerApp("camera-to-file", source, sink)
            self.pipeline.run()

        return None

    def stop_streaming(self) -> Exception|None:
        """
        Stop streaming.
        """
        self._switch_to_this_camera()

        if PICAMERA_ENABLED:
            self.camera.stop_recording()
        else:
            self.pipeline.shutdown()

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
