import unittest
from . import testutils
from ..src.podapp.libraries.coprocessors import mcu

@unittest.skipIf(testutils.in_wsl_mode(), "Running in WSL mode")
class TestMCU(unittest.TestCase):
    """
    Tests to make sure the sensor controller is working.
    """
    # Nothing to do yet
    pass

def gather() -> unittest.TestSuite:
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(TestMCU)
