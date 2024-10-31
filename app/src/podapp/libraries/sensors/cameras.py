"""
This module provides high-level API functions
for the cameras in the system.
"""
from picamera2.encoders import H264Encoder
from picamera2 import Picamera2
from typing import Any
from typing import Dict
from ..common import error
from ..common import log
import RPi.GPIO as GPIO

# TODO: This whole module is going to need to be reconsidered when I get around to dealing with the camera mux

class Camera:
    """
    The `Camera` class provides high-level functionality for a camera hardware module.
    """
    def __init__(self, config: Dict[str, Any], config_name: str) -> None:
        cam_id = str(config['pinconfig']['cameras'][config_name]['id'])
        self.cam_mux = str(config['pinconfig']['cameras']['camera-mux']['pin'])
        self.mux_level = getattr(GPIO, str(config['pinconfig']['cameras'][config_name]['mux-active-level']))

        # Set up the camera mux pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.cam_mux, GPIO.OUT)

        # Collect camera info
        GPIO.output(self.cam_mux, GPIO.LOW)
        attached_cameras_info0 = Picamera2.global_camera_info()
        GPIO.output(self.cam_mux, GPIO.HIGH)
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
        GPIO.output(self.cam_mux, self.mux_level)

    def shutdown(self) -> None:
        """
        Clean shutdown function.
        """
        self.stop_streaming()
        GPIO.cleanup(self.cam_mux)

    def stream_to_file(self, fpath: str) -> Exception|None:
        """
        Asynchronously stream to a file.
        """
        self._switch_to_this_camera()

        video_config = self.camera.create_video_configuration()
        self.camera.configure(video_config)
        encoder = H264Encoder(bitrate=10000000)
        self.camera.start_recording(encoder, fpath)
        return None

    def stop_streaming(self) -> Exception|None:
        """
        Stop streaming.
        """
        self._switch_to_this_camera()

        self.camera.stop_recording()
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
