"""
This module provides some high-level functions
for controlling the display.
"""
from typing import Any
from typing import Dict
from typing import Tuple
from ..common import error
import re
import subprocess

class Display:
    """
    The `Display` class should be used as a singleton
    for controlling the display.
    """
    def __init__(self, config: Dict[str, Any]) -> None:
        self.touch_i2c_sda_pin = int(config['pinconfig']['screen']['i2c-sda']['pin'])
        self.touch_i2c_scl_pin = int(config['pinconfig']['screen']['i2c-scl']['pin'])
        self.timeout_seconds = int(config['moduleconfig']['screen']['timeout-seconds'])
        self.dsi_id = config['pinconfig']['screen']['dsi']['id']

    def shutdown(self) -> None:
        """
        Clean shutdown function.
        """
        # TODO
        pass

    def on(self) -> Tuple[Exception|None, bool|None]:
        """
        Is the screen on?
        """
        p = subprocess.run("wlr-randr", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=self.timeout_seconds, encoding='utf-8')
        if p.returncode == 0:
            found_id = False
            for line in p.stdout.splitlines():
                if line.strip().startswith(self.dsi_id):
                    found_id = True
                if found_id and line.strip().startswith("Enabled:"):
                    return (None, line.strip().split()[-1] == "yes")
            return (error.SubprocessException(f"Could not find DSI identifier {self.dsi_id} in wlr-randr output. Output: {p.stdout}"), None)
        else:
            return (error.SubprocessException(f"Non-zero return code running 'xset -q': {p.stdout}"), None)

    def off(self) -> Tuple[Exception|None, bool|None]:
        """
        Is the screen off?
        """
        err, on = self.on()
        return (err, not on)

    def turn_on(self) -> Exception|None:
        """
        Turn on the screen. Does not block.
        """
        p = subprocess.run(f"wlr-randr --output {self.dsi_id} --on".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=self.timeout_seconds, encoding='utf-8')
        if p.returncode != 0:
            return error.SubprocessException(f"Non-zero return code running 'xset dpms force on': {p.stdout}")
        else:
            return None

    def turn_off(self) -> Exception|None:
        """
        Turn off the screen. Does not block.
        """
        # TODO: This does not turn off the touch interface
        p = subprocess.run(f"wlr-randr --output {self.dsi_id} --off".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=self.timeout_seconds, encoding='utf-8')
        if p.returncode != 0:
            return error.SubprocessException(f"Non-zero return code running 'xset dpms force off': {p.stdout}")
        else:
            return None
