"""
This module provides some high-level functions
for controlling the display.
"""
from typing import Any
from typing import Dict
import subprocess

class Display:
    """
    The `Display` class should be used as a singleton
    for controlling the display.
    """
    def __init__(self, config: Dict[str, Any]) -> None:
        pass

    @property
    def on(self) -> bool:
        """
        Is the screen on?
        """
        p = subprocess.run("xset -q".split(), capture_output=True)
        # TODO: We shouldn't just crash
        p.check_returncode()
        # TODO: Check p's stdout.decode() for a regular expression
        return False

    @property
    def off(self) -> bool:
        """
        Is the screen off?
        """
        return not self.on

    def turn_on(self) -> None:
        """
        Turn on the screen.
        """
        p = subprocess.run("xset dpms force on".split(), capture_output=True)
        # TODO: We shouldn't just crash
        p.check_returncode()

    def turn_off(self) -> None:
        """
        Turn off the screen.
        """
        p = subprocess.run("xset dpms force off".split(), capture_output=True)
        # TODO: We shouldn't just crash
        p.check_returncode()
