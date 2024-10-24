"""
"""
from ..libraries.common import appconfig
from ..libraries.coprocessors import ai
from ..libraries.coprocessors import mcu
from ..libraries.outputs import leds
from ..libraries.outputs import screen
from ..libraries.sensors import cameras
import os

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

    # Initialize all the hardware singletons
    hailoproc = ai.AICoprocessor(config)
    flashlight = leds.FlashLight(config)
    display = screen.Display(config)
    front_camera = cameras.Camera()  # TODO
    rear_camera = cameras.Camera()   # TODO

    # For now, run a simple sequence to test the power draw
    power_draw_idle = _read_power_number()
    ## Screen
    display.turn_on()
    power_draw_screen_only = _read_power_number()
    display.turn_off()
    ## Camera
    video_fpath = "./scratch-video.mp4"
    front_camera.stream_to_file(video_fpath)
    power_draw_camera_only = _read_power_number()
    front_camera.stop()
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
    front_camera.stop()
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
