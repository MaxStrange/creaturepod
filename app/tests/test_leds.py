import time
import unittest
from . import testutils
from ..src.podapp.libraries.outputs import leds

class TestLEDs(unittest.TestCase):
    """
    Tests to make sure the LEDs are working.
    """
    def setUp(self) -> None:
        self.config = testutils.load_config()
        self.flashlight = leds.FlashLight(self.config)
        self.strips = leds.LEDStrips(self.config)
        return super().setUp()

    def tearDown(self) -> None:
        self.flashlight.shutdown()
        self.strips.shutdown()
        return super().tearDown()

    @unittest.skip("TODO")
    def test_flashlight_on(self):
        """Test that we can turn on the flashlight without breaking anything."""
        self.flashlight.turn_on()
        self.assertTrue(self.flashlight.on)

    def test_flashlight_off(self):
        """Test that we can turn off the flashlight without breaking anything."""
        self.flashlight.turn_on()
        time.sleep(0.5)
        self.flashlight.turn_off()
        self.assertTrue(self.flashlight.off)

def gather() -> unittest.TestSuite:
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(TestLEDs)
