import os
import time
import unittest
from . import testutils
from ..src.podapp.libraries.sensors import cameras
from ..src.podapp.libraries.gstreamer_utils import utils as gst_utils

@unittest.skipIf(testutils.in_wsl_mode(), "Cannot access cameras from WSL without a lot of hassle")
class TestCameras(unittest.TestCase):
    """
    Tests to make sure the cameras work.
    """
    test_fpath_front = "front.h264"
    test_fpath_rear = "rear.h264"

    def setUp(self) -> None:
        self.config = testutils.load_config()
        gst_utils.configure(self.config)
        self.front_camera = cameras.FrontCamera(self.config)
        self.rear_camera = cameras.RearCamera(self.config)
        return super().setUp()

    def tearDown(self) -> None:
        self.front_camera.shutdown()
        self.rear_camera.shutdown()
        if os.path.isfile(self.test_fpath_front):
            os.remove(self.test_fpath_front)
        if os.path.isfile(self.test_fpath_rear):
            os.remove(self.test_fpath_rear)
        return super().tearDown()

    def test_recording_to_file(self):
        """Test that the cameras can record to a file."""
        for orientation in ("front", "rear"):
            with self.subTest(camera=orientation):
                if orientation == "front":
                    cam = self.front_camera
                    fpath = self.test_fpath_front
                else:
                    cam = self.rear_camera
                    fpath = self.test_fpath_rear

                err = cam.stream_to_file(fpath)
                self.assertIsNone(err)
                time.sleep(1)
                err = cam.stop_streaming()
                self.assertIsNone(err)

    def test_streaming_to_display(self):
        """Test that the cameras can live-stream to the screen."""
        for orientation in ("front", "rear"):
            with self.subTest(camera=orientation):
                if orientation == "front":
                    cam = self.front_camera
                else:
                    cam = self.rear_camera

                err = cam.stream_to_display()
                self.assertIsNone(err)
                time.sleep(1)
                err = cam.stop_streaming()
                self.assertIsNone(err)

def gather() -> unittest.TestSuite:
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(TestCameras)
