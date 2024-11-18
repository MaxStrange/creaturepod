import unittest
from . import test_ai

def gather():
    suite = unittest.TestSuite()
    suite.addTest(test_ai.gather())
    return suite

if __name__ == '__main__':
    suite = gather()
    runner = unittest.TextTestRunner()
    runner.run(suite)
