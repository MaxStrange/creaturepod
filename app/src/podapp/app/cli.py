"""
CLI entry to the application. Useful for testing and for turning on/off various
components.
"""
from .. import __version__
from ..libraries.common import appconfig
from ..libraries.common import log
from ..libraries.gstreamer_utils import utils as gst_utils
from ..libraries.coprocessors import ai
from ..libraries.outputs import leds
from ..libraries.outputs import screen
from ..libraries.sensors import cameras
import click

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-c', "--config", type=click.Path(exists=True, dir_okay=False, resolve_path=True, allow_dash=False), default=appconfig.DEFAULT_CONFIG_FILE_PATH, help="Path to a configuration file.")
@click.option('-l', "--log-level", type=click.Choice(log.ALLOWED_LEVELS), default=None, help="Log level override. We use this instead of the config file's value if passed.")
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx, config, log_level):
    ctx.ensure_object(dict)

    # Get the configuration file if provided
    config = appconfig.load_config_file(config)
    
    # Initialize logging
    if log_level is not None:
        config['moduleconfig']['logging']['log-level'] = log_level
    log.init(config)
    log.enable_logging_to_console(config)

    # Initialize fundamental systems
    gst_utils.configure(config)

    # Attach the configuration to the context
    ctx.obj['config'] = config

#########################################################################################################
####################### AI COMMANDS #################################################################
#########################################################################################################
@cli.group(name="ai")
@click.pass_context
def ai_group(ctx):
    pass

@ai_group.command(name="infer")
@click.argument("model", type=click.Choice([model_type.value for model_type in ai.AIModelType]), required=True)
@click.option('-s', "source", type=click.STRING, required=True, help="A path to a file or one of ('rear-camera', 'front-camera')")
@click.option('-o', "--outfpath", type=click.Path(dir_okay=False, writable=True, resolve_path=True), default=None, help="If given, we save an output file at this location. Otherwise, we attempt to display to screen.")
@click.pass_context
def ai_infer(ctx, model, source, outfpath):
    config = ctx.obj['config']
    hailoproc = ai.AICoprocessor(config)

    err = hailoproc.set_source(source)
    if err:
        return err

    err = hailoproc.set_model(ai.AIModelType(model))
    if err:
        return err

    err = hailoproc.set_sinks(outfpath if outfpath is not None else "display")
    if err:
        return err

    hailoproc.start()

#########################################################################################################
####################### LED COMMANDS #################################################################
#########################################################################################################
@cli.group(name="led")
@click.pass_context
def led_group(ctx):
    pass

@led_group.command(name="fl-on")
@click.pass_context
def led_flashlight_on(ctx):
    """
    Turn on the flashlight.
    """
    config = ctx.obj['config']
    flashlight = leds.FlashLight(config)

    err = flashlight.turn_on()
    return err

@led_group.command(name="fl-off")
@click.pass_context
def led_flashlight_off(ctx):
    """
    Turn off the flashlight.
    """
    config = ctx.obj['config']
    flashlight = leds.FlashLight(config)

    err = flashlight.turn_off()
    return err

#########################################################################################################
####################### DISPLAY COMMANDS #################################################################
#########################################################################################################
@cli.group(name="display")
@click.pass_context
def display_group(ctx):
    pass

@display_group.command(name="on")
@click.pass_context
def display_on(ctx):
    """
    Turn on the display.
    """
    config = ctx.obj['config']
    dis = screen.Display(config)

    err = dis.turn_on()
    return err

@display_group.command(name="off")
@click.pass_context
def display_off(ctx):
    """
    Turn off the display.
    """
    config = ctx.obj['config']
    dis = screen.Display(config)

    err = dis.turn_off()
    return err

#########################################################################################################
####################### CAMERA COMMANDS #################################################################
#########################################################################################################
@cli.group(name="camera")
@click.argument("camera", type=click.Choice("front", "rear"), default="front", required=True)
@click.pass_context
def camera_group(ctx, camera):
    ctx.obj['camera'] = "front-camera" if camera == 'front' else 'rear-camera'

@camera_group.command(name="record")
@click.argument("fpath", type=click.Path(dir_okay=False))
@click.pass_context
def camera_record(ctx, fpath):
    """
    Turn on the camera and record the given number of seconds. Records to the given file in mp4 format.
    """
    cam = ctx.obj['camera']
    config = ctx.obj['config']
    if cam == "front-camera":
        camera_device = cameras.FrontCamera(config)
    else:
        camera_device = cameras.RearCamera(config)

    err = camera_device.stream_to_file(fpath)
    return err

if __name__ == "__main__":
    cli()
