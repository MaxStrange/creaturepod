"""
This module provides some high-level functions
for controlling the display.
"""
from typing import Any
from typing import Dict

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
        # TODO
        pass

    def turn_off(self) -> None:
        """
        Turn off the screen.
        """
        # TODO
        pass
