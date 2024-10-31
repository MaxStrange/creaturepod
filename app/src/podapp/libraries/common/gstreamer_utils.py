"""
Provides utilities for building and running GStreamer pipelines.
"""
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

        # TODO: Remove elements here that we don't need/want
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
    def __init__(self, source: GStreamerSource) -> None:
        self.video_source = self.options_menu.input
        self.source_type = get_source_type(self.video_source)
        self.user_data = user_data
        self.video_sink = "xvimagesink"
        self.pipeline = None
        self.loop = None

        # Set Hailo parameters; these parameters should be set based on the model used
        self.batch_size = 1
        self.network_width = 640
        self.network_height = 640
        self.network_format = "RGB"
        self.hef_path = None
        self.app_callback = None

        # Set user data parameters
        user_data.use_frame = self.options_menu.use_frame

        self.sync = "false" if (self.options_menu.disable_sync or self.source_type != "file") else "true"
        self.show_fps = "true" if self.options_menu.show_fps else "false"

        if self.options_menu.dump_dot:
            os.environ["GST_DEBUG_DUMP_DOT_DIR"] = self.current_path

    def on_fps_measurement(self, sink, fps, droprate, avgfps):
        print(f"FPS: {fps:.2f}, Droprate: {droprate:.2f}, Avg FPS: {avgfps:.2f}")
        return True

    def create_pipeline(self):
        # Initialize GStreamer
        Gst.init(None)

        pipeline_string = self.get_pipeline_string()
        try:
            self.pipeline = Gst.parse_launch(pipeline_string)
        except Exception as e:
            print(e)
            print(pipeline_string)
            sys.exit(1)

        # Connect to hailo_display fps-measurements
        if self.show_fps:
            print("Showing FPS")
            self.pipeline.get_by_name("hailo_display").connect("fps-measurements", self.on_fps_measurement)

        # Create a GLib Main Loop
        self.loop = GLib.MainLoop()

    def bus_call(self, bus, message, loop):
        t = message.type
        if t == Gst.MessageType.EOS:
            print("End-of-stream")
            self.on_eos()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"Error: {err}, {debug}")
            self.shutdown()
        # QOS
        elif t == Gst.MessageType.QOS:
            # Handle QoS message here
            qos_element = message.src.get_name()
            print(f"QoS message received from {qos_element}")
        return True


    def on_eos(self):
        if self.source_type == "file":
             # Seek to the start (position 0) in nanoseconds
            success = self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, 0)
            if success:
                print("Video rewound successfully. Restarting playback...")
            else:
                print("Error rewinding the video.")
        else:
            self.shutdown()


    def shutdown(self, signum=None, frame=None):
        print("Shutting down... Hit Ctrl-C again to force quit.")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.pipeline.set_state(Gst.State.PAUSED)
        GLib.usleep(100000)  # 0.1 second delay

        self.pipeline.set_state(Gst.State.READY)
        GLib.usleep(100000)  # 0.1 second delay

        self.pipeline.set_state(Gst.State.NULL)
        GLib.idle_add(self.loop.quit)


    def get_pipeline_string(self):
        # This is a placeholder function that should be overridden by the child class
        return ""

    def dump_dot_file(self):
        print("Dumping dot file...")
        Gst.debug_bin_to_dot_file(self.pipeline, Gst.DebugGraphDetails.ALL, "pipeline")
        return False

    def run(self):
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
    if 'gstreamer-utils' not in config:
        return

    gstreamer_config = config['gstreamer-utils']

    if 'queue-params' in gstreamer_config:
        leaky = gstreamer_config['queue-params'].get('leaky', QUEUE_PARAMS.leaky)
        max_buffers = gstreamer_config['queue-params'].get('max-buffers', QUEUE_PARAMS.max_buffers)
        max_bytes = gstreamer_config['queue-params'].get('max-bytes', QUEUE_PARAMS.max_bytes)
        max_time = gstreamer_config['queue-params'].get('max-time', QUEUE_PARAMS.max_time)
        QUEUE_PARAMS = QueueParams(leaky=leaky, max_buffers=max_buffers, max_bytes=max_bytes, max_time=max_time)
