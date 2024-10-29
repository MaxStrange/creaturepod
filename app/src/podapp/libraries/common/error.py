"""
Custom errors.
"""

class CreaturePodException(Exception):
    """
    Base class for all custom exceptions in this application.
    """
    pass

class SubprocessException(CreaturePodException):
    """
    An exception that indicates a non-zero return code.
    """
    pass
