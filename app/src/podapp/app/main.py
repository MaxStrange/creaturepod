"""
"""
from ..libraries.common import appconfig
from ..libraries.common import gstreamer_utils
from ..libraries.common import log
from ..libraries.coprocessors import ai
from ..libraries.coprocessors import mcu
from ..libraries.outputs import leds
from ..libraries.outputs import screen
from ..libraries.sensors import cameras
from typing import Any
from typing import List
import functools
import os
import signal

def _clean_exit(hardware_objects: List[Any]):
    """
    Shut down the application cleanly by calling 'shutdown()' on each object.
    """
    log.info("CTRL-C being handled. Shutting down all hardware objects...")
    for o in hardware_objects:
        if hasattr(o, 'shutdown'):
            o.shutdown()

def _read_power_number() -> float:
    power_val = None
    while power_val is None:
        power_val_raw = input("Enter power value: ")
        try:
            power_val = float(power_val_raw.strip())
        except ValueError:
            print("Cannot interpret the input as a number.")
    return power_val

def main():
    # Parse the config file
    config = appconfig.load_config_file()

    # Set up logging
    log.init(config)
    log.enable_logging_to_console(config)

    # Initialize fundamental systems
    gstreamer_utils.configure(config)

    # Initialize all the hardware singletons
    hailoproc = ai.AICoprocessor(config)
    flashlight = leds.FlashLight(config)
    display = screen.Display(config)
    front_camera = cameras.FrontCamera(config)
    rear_camera = cameras.RearCamera(config)

    # Set up signal handler for SIGINT (Ctrl-C)
    signal_handler = functools.partial(_clean_exit, hardware_objects=[hailoproc, flashlight, display, front_camera, rear_camera])
    signal.signal(signal.SIGINT, signal_handler)

    # For now, run a simple sequence to test the power draw
    power_draw_idle = _read_power_number()

    ## Screen
    err = display.turn_on()
    if err:
        log.error(f"Error when turning on the display: {err}")

    power_draw_screen_only = _read_power_number()

    err = display.turn_off()
    if err:
        log.error(f"Error when turning off the display: {err}")

    ## Camera
    video_fpath = "./scratch-video.h264"
    err = front_camera.stream_to_file(video_fpath)
    if err:
        log.error(f"Error when trying to stream the camera output to a file: {err}")

    power_draw_camera_only = _read_power_number()

    err = front_camera.stop_streaming()
    if err:
        log.error(f"Error when trying to stop the camera: {err}")

    ## AI Module
    hailoproc.load_model("./TODO")
    hailoproc.inference_on_file(video_fpath, loop=True)
    power_draw_hailo_only = _read_power_number()
    hailoproc.stop()

    ## All at once
    display.turn_on()
    stream_handle = front_camera.stream_to_coprocessor()
    hailoproc.inference_on_stream(stream_handle)
    power_draw_experimental_total = _read_power_number()
    hailoproc.stop()
    front_camera.shutdown()
    display.turn_off()

    # Clean up after ourselves
    os.remove(video_fpath)

    summed_total = sum([power_draw_screen_only - power_draw_idle, power_draw_camera_only - power_draw_idle, power_draw_hailo_only - power_draw_idle])
    print("Totals:")
    print(f"  Screen..............  {power_draw_screen_only}")
    print(f"  Camera..............  {power_draw_camera_only}")
    print(f"  AI Module...........  {power_draw_hailo_only}")
    print(f"  Calculated Total....  {summed_total}")
    print(f"  Experimental Total..  {power_draw_experimental_total}")

if __name__ == "__main__":
    main()
