"""
Module to keep all GPIO dependencies in one place (which should help with dev/testing).

All pins are numbered according to BCM.
"""
import enum

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO_ENABLED = True
except ImportError:
    GPIO_ENABLED = False

class Direction(enum.IntEnum):
    """
    Directions for pins.
    """
    OUT        = 0
    IN         = 1
    UNASSIGNED = 2

class Level(enum.IntEnum):
    """
    Levels for pins.
    """
    LOW      = 0
    HIGH     = 1
    TRISTATE = 2

class Pin:
    """
    An object to represent the configuration and state of a pin
    in case we don't have the GPIO library installed (for testing/development).
    """
    def __init__(self, pin_number: int) -> None:
        self.number = pin_number
        self.direction = Direction.IN
        self.level = Level.TRISTATE

# Pin Dict for debug
pin_dict = {i: Pin(i) for i in range(2, 26+1)}

def configure_pin(pin: int, direction: Direction):
    """
    Configure the given pin with the given direction.
    """
    if GPIO_ENABLED:
        GPIO.setup(pin, direction)
    else:
        pin_dict[pin].direction = direction

def output(pin: int, level: Level):
    """
    Set the given pin to the given level.
    """
    if GPIO_ENABLED:
        GPIO.output(pin, level)
    else:
        pin_dict[pin].level = level

def deconfigure_pin(pin: int):
    """
    Clean up the given pin.
    """
    if GPIO_ENABLED:
        GPIO.cleanup(pin)
    else:
        pin_dict[pin].direction = Direction.IN
