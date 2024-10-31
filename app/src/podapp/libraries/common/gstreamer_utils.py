"""
Provides utilities for building and running GStreamer pipelines.

Much code in this module was based on HAILO AI examples, with heavy modification.
"""
from ..common import log
from typing import Any
from typing import Dict
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gst
import os
import collections

# TODO: Add audio support

# Some default parameters for the gst queues. These can be overridden by the application configuration.
QueueParams = collections.namedtuple("QueueParams", "max_buffers max_bytes max_time leaky")
QUEUE_PARAMS = QueueParams(max_buffers=3, max_bytes=0, max_time=0, leaky='no')

class GStreamerSource:
    """
    A class to encapsulate a GStreamer source that can be added into a pipeline.
    """
    def __init__(self, source_uri: str, video_format="RGB", video_width=640, video_height=640, name="source") -> None:
        """
        Create an instance of a GStreamerSource that can be added to a pipeline.

        Note that the arguments supplied to this function should be the ones that come out of the
        source - not the desired ones. If you want to scale or otherwise adjust the video frames
        after retrieving them from the source, you should do that in a preprocess element.

        Args
        ----
        - `source_uri`: (`str`) The URI for the source of video. A camera ID like 'cam0' as found
           in the appconfig YAML file will be treated as a Raspberry Pi camera module coming over the
           corresponding (0 or 1) CSI port.
        - `video_format`: (`str`) The format of the video. See the GStreamer pad documentation for your source.
        - `video_width`: (`int`) The width (in pixels) of the video.
        - `video_height`: (`int`) The height (in pixels) of the video.
        - `name`: (`str`) The name of the source element for debugging.
        """
        if os.path.exists(source_uri):
            # Source is a file (note that this will have to be updated if we ever support devices found in /dev/*)
            source_element = (
                f'filesrc location="{source_uri}" name={name} ! '
                f'queue name=f"{name}_queue_dec264" leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
                f'qtdemux ! h264parse ! avdec_h264 max-threads=2 ! '
            )
        elif source_uri == "cam0" or source_uri == "cam1":
            # Source is CSI camera interface
             source_element = (
                f'libcamerasrc name={name} ! '
                f'video/x-raw, format={video_format}, width={video_width}, height={video_height} ! '
            )
        else:
            # RTSP camera or something. Not currently supported.
            raise ValueError(f"Given a source_uri that is not supported: {source_uri}")

        # TODO: Remove elements here that we don't need/want. E.g., the videoscale and videoconvert portions don't seem to do anything. Verify and remove them.
        self.element_pipeline = (
            f'{source_element} '
            f'queue name=f"{name}_queue_scale" leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
            f'videoscale name={name}_videoscale n-threads=2 ! '
            f'queue name=f"{name}_queue_convert" leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
            f'videoconvert n-threads=3 name={name}_convert qos=false ! '
            f'video/x-raw, format={video_format}, pixel-aspect-ratio=1/1 ! '
            # f'video/x-raw, format={video_format}, width={video_width}, height={video_height} ! '
        )

class GStreamerApp:
    def __init__(self, name: str, source: GStreamerSource) -> None:
        self.name = name
        self.source = source
        self.repeat_on_end_of_stream = False

        # Create the pipeline
        Gst.init(None)
        pipeline_string = " ! ".join([self.source.element_pipeline])
        self.pipeline = Gst.parse_launch(pipeline_string)

        # Save dot file (if desired)
        if os.environ.get("GST_DEBUG_DUMP_DOT_DIR", None) is not None:
            Gst.debug_bin_to_dot_file(self.pipeline, Gst.DebugGraphDetails.ALL, self.name)

        # Create the mainloop
        self.loop = GLib.MainLoop()

    def _handle_end_of_stream(self) -> bool:
        """
        Attempt to handle EOS. Return success or not. Loop from the beginning
        of the stream if `self.repeat_on_end_of_stream`, otherwise just shut down
        the pipeline.
        """
        if self.repeat_on_end_of_stream:
             # Seek to the start (position 0) in nanoseconds
            success = self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, 0)
        else:
            self.shutdown()
            success = True

        if not success:
            log.error(f"Could not rewind pipeline {self.name}")

        return success

    def bus_call(self, bus, message, loop) -> bool:
        """
        Handler for GStreamer bus messages.

        See: https://gstreamer.freedesktop.org/documentation/additional/design/messages.html?gi-language=c
        """
        match message.type:
            case Gst.MessageType.EOS:
                # End of stream
                return self._handle_end_of_stream()
            case Gst.MessageType.INFO:
                # An info debug message ocurred in the pipeline
                info, debug = message.parse_warning()
                log.info(f"Info in the GStreamer pipeline {self.name}: {info}, {debug}")
                return True
            case Gst.MessageType.WARNING:
                # A warning ocurred in the pipeline
                warning, debug = message.parse_warning()
                log.warning(f"Warning in the GStreamer pipeline {self.name}: {warning}, {debug}")
                return True
            case Gst.MessageType.ERROR:
                # An error ocurred in the pipeline
                err, debug = message.parse_error()
                log.error(f"Error in the GStreamer pipeline {self.name}: {err}, {debug}")
                self.shutdown()
                return True
            case Gst.MessageType.QOS:
                # Quality of streaming notification
                qos_element = message.src.get_name()
                log.warning(f"Quality of service message received from pipeline {self.name}, element {qos_element}. Message: {message.get_details()}")
                return True
            case Gst.MessageType.STREAM_STATUS:
                # A change in the stream status
                status, owner = message.parse_stream_status()
                log.info(f"Stream status changed in pipeline {self.name}: {status}. Owner: {owner}")
                return True
            case Gst.MessageType.ELEMENT:
                # Element-specific bus message. Potentially could want a handler.
                # TODO: Add element-wise handlers?
                log.info(f"Pipeline {self.name} received an element-specific message from {message.src.get_name()}: {message.get_details()}")
                return True
            case _:
                # There are a ton of possible message types. Mostly just ignore them and pretend like we handled them.
                log.debug(f"Received a bus message that we do not handle on pipeline {self.name}: {message.get_details()}")
                return True

    def shutdown(self, signum=None, frame=None):
        """
        Clean shutdown.
        """
        self.pipeline.set_state(Gst.State.PAUSED)
        GLib.usleep(100000)  # 0.1 second delay

        self.pipeline.set_state(Gst.State.READY)
        GLib.usleep(100000)  # 0.1 second delay

        self.pipeline.set_state(Gst.State.NULL)
        GLib.idle_add(self.loop.quit)

    def run(self, repeat_on_end_of_stream=False):
        """
        Run the pipeline. Argument `repeat_on_end_of_stream` most likely only makes
        sense (and will probably only work) in the case of a file input source.
        """
        self.repeat_on_end_of_stream = repeat_on_end_of_stream



        # Add a watch for messages on the pipeline's bus
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.bus_call, self.loop)

        # Connect pad probe to the identity element
        identity = self.pipeline.get_by_name("identity_callback")
        if identity is None:
            print("Warning: identity_callback element not found, add <identity name=identity_callback> in your pipeline where you want the callback to be called.")
        else:
            identity_pad = identity.get_static_pad("src")
            identity_pad.add_probe(Gst.PadProbeType.BUFFER, self.app_callback, self.user_data)

        hailo_display = self.pipeline.get_by_name("hailo_display")
        if hailo_display is None:
            print("Warning: hailo_display element not found, add <fpsdisplaysink name=hailo_display> to your pipeline to support fps display.")
        else:
            xvimagesink = hailo_display.get_by_name("xvimagesink0")
            if xvimagesink is not None:
                xvimagesink.set_property("qos", False)

        # Disable QoS to prevent frame drops
        disable_qos(self.pipeline)

        # Start a subprocess to run the display_user_data_frame function
        if self.options_menu.use_frame:
            display_process = multiprocessing.Process(target=display_user_data_frame, args=(self.user_data,))
            display_process.start()

        # Set pipeline to PLAYING state
        self.pipeline.set_state(Gst.State.PLAYING)

        # Dump dot file
        if self.options_menu.dump_dot:
            GLib.timeout_add_seconds(3, self.dump_dot_file)

        # Run the GLib event loop
        self.loop.run()

        # Clean up
        self.user_data.running = False
        self.pipeline.set_state(Gst.State.NULL)
        if self.options_menu.use_frame:
            display_process.terminate()
            display_process.join()

def configure(config: Dict[str, Any]):
    """
    Configure the gstreamer utils.
    """
    if 'gstreamer-utils' not in config['moduleconfig']:
        return

    gstreamer_config = config['moduleconfig']['gstreamer-utils']

    # Queue params
    if 'queue-params' in gstreamer_config:
        leaky = gstreamer_config['queue-params'].get('leaky', QUEUE_PARAMS.leaky)
        max_buffers = gstreamer_config['queue-params'].get('max-buffers', QUEUE_PARAMS.max_buffers)
        max_bytes = gstreamer_config['queue-params'].get('max-bytes', QUEUE_PARAMS.max_bytes)
        max_time = gstreamer_config['queue-params'].get('max-time', QUEUE_PARAMS.max_time)
        QUEUE_PARAMS = QueueParams(leaky=leaky, max_buffers=max_buffers, max_bytes=max_bytes, max_time=max_time)

    # Dot graph (the GStreamer pipeline can print itself to a dot file)
    if 'dot-graph' in gstreamer_config and gstreamer_config['dot-graph']['save']:
        dpath = gstreamer_config['dot-graph']['dpath']
        if os.path.isdir(dpath):
            os.environ["GST_DEBUG_DUMP_DOT_DIR"] = dpath
        else:
            log.warning(f"Config file's moduleconfig->gstreamer-utils->dot-graph->dpath does not point to a directory. Given {dpath}")

def source_uri_valid(source_uri: str) -> bool:
    """
    Return whether the given source URI is valid.
    """
    if os.path.isfile(source_uri):
        return True
    elif source_uri == "cam0":
        return True
    elif source_uri == "cam1":
        return True
    else:
        return False
