import time
import unittest
from . import testutils
from ..src.podapp.libraries.outputs import screen

@unittest.skipIf(testutils.in_wsl_mode(), "Cannot use screen in WSL mode")
class TestScreen(unittest.TestCase):
    """
    Tests to make sure the screen works.
    """
    def setUp(self) -> None:
        self.config = testutils.load_config()
        self.display = screen.Display(self.config)
        return super().setUp()

    def tearDown(self) -> None:
        self.display.turn_on()
        self.display.shutdown()
        return super().tearDown()

    def test_screen_on(self):
        """Test that we can turn on the screen without breaking anything."""
        err = self.display.turn_on()
        self.assertIsNone(err)

        err, on = self.display.on()
        self.assertIsNone(err)
        self.assertTrue(on)

        err, off = self.display.off()
        self.assertIsNone(err)
        self.assertFalse(off)

    def test_screen_off(self):
        """Test that we can turn off the screen without breaking anything."""
        err = self.display.turn_off()
        self.assertIsNone(err)

        time.sleep(1)

        err, off = self.display.off()
        self.assertIsNone(err)
        self.assertTrue(off)

        err, on = self.display.on()
        self.assertIsNone(err)
        self.assertFalse(on)

def gather() -> unittest.TestSuite:
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(TestScreen)
