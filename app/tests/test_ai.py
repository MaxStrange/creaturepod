import time
import unittest
from . import testutils
from ..src.podapp.libraries.coprocessors import ai
from ..src.podapp.libraries.gstreamer_utils import utils as gst_utils

@unittest.skipIf(testutils.in_wsl_mode(), "Running in WSL mode")
class TestAI(unittest.TestCase):
    """
    Tests to make sure the AI coprocessor is working.
    """
    def setUp(self):
        self.config = testutils.load_config()
        testutils.initialize_logger(self.config)
        gst_utils.configure(self.config)
        self.coproc = ai.AICoprocessor(self.config)

        # Set up sources
        self.sources = []
        if self.config['pinconfig']['cameras']['front-camera']['enabled']:
            self.sources += [self.config['pinconfig']['cameras']['front-camera']['id']]
        if self.config['pinconfig']['cameras']['rear-camera']['enabled']:
            self.sources += [self.config['pinconfig']['cameras']['rear-camera']['id']]
        #self.sources += ["test_video.mp4"]  # TODO
        #self.sources += ["test_video.h264"] # TODO
        #self.sources += ["test_video.mov"]  # TODO
        # TODO RTSP

        # Set up sinks
        #self.sinks = ["test_output.h264", "display"]  # TODO: RTSP
        self.sinks = ["test_output.h264"]

        return super().setUp()

    def tearDown(self):
        self.coproc.shutdown()
        return super().tearDown()

    def _setup_pipeline(self, source: str, model_type: ai.AIModelType, *sinks):
        err = self.coproc.set_source(source)           
        self.assertIsNone(err)

        err = self.coproc.set_model(model_type)
        self.assertIsNone(err)

        err = self.coproc.set_sinks(*sinks)
        self.assertIsNone(err)

    def _run_pipeline_and_reset_it(self, delay_s=0.5):
        self.coproc.start()
        time.sleep(delay_s)
        self.coproc.stop()
        self.coproc.clear()

    def _matrix(self, model_type: ai.AIModelType):
        for source in self.sources:
            for sink in self.sinks:
                with self.subTest(source=source, sink=sink):
                    self._setup_pipeline(source, model_type, sink)
                    self._run_pipeline_and_reset_it()

    def test_object_detection_yolov8(self):
        """Test that YOLOv8 doesn't crash"""
        self._matrix(ai.AIModelType.OBJECT_DETECTION_YOLO_V8)
                    
    def test_instance_segmentation(self):
        """Test that instance segmentation doesn't crash"""
        self._matrix(ai.AIModelType.INSTANCE_SEGMENTATION)

    def test_pose_estimation(self):
        """Test that pose estimation doesn't crash"""
        self._matrix(ai.AIModelType.POSE_ESTIMATION)

    def test_multiple_sinks(self):
        """Test that each type of model can run with at least two different sinks without crashing"""
        source = self.sources[0]
        sinks = self.sinks[0, 1]
        for model_type in ai.AIModelType:
            with self.subTest(source=source, model_type=model_type, sinks=sinks):
                self._setup_pipeline(source, model_type, *sinks)
                self._run_pipeline_and_reset_it()

def gather() -> unittest.TestSuite:
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(TestAI)
