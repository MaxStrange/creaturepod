"""
This module is responsible for the LEDs present in the pod.
"""
from ..coprocessors import mcu
from typing import Any
from typing import Dict

class FlashLight:
    """
    The `FlashLight` class should be a singleton
    that is responsible for the flashlight LED in the system.
    """
    def __init__(self, config: Dict[str, Any]) -> None:
        pass

    @property
    def on(self) -> bool:
        """
        Is the LED on?
        """
        return False

    @property
    def off(self) -> bool:
        """
        Is the LED off?
        """
        return not self.on

    def turn_on(self) -> None:
        """
        Turn on the LED.
        """
        # TODO
        pass

    def turn_off(self) -> None:
        """
        Turn off the LED.
        """
        # TODO
        pass

class LEDStrips:
    """
    The `LEDStrips` class should be a singleton
    that is responsible for the LED strips in the system.
    """
    def __init__(self, config: Dict[str, Any]) -> None:
        pass
