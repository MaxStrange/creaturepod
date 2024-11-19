import unittest
from . import test_ai
from . import test_cameras
from . import test_leds
from . import test_mcu
from . import test_screen

def gather():
    suite = unittest.TestSuite()
    suite.addTest(test_ai.gather())
    suite.addTest(test_cameras.gather())
    suite.addTest(test_leds.gather())
    suite.addTest(test_mcu.gather())
    suite.addTest(test_screen.gather())
    return suite

if __name__ == '__main__':
    suite = gather()
    runner = unittest.TextTestRunner()
    runner.run(suite)
