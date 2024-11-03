"""
Provides utilities for building and running GStreamer pipelines.

Much code in this module was based on HAILO AI examples, with heavy modification.
"""
from ..common import log
from typing import Any
from typing import Dict
from typing import List
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gst
import os
import collections
import urllib

# TODO: Add audio support
# TODO: Double check the exclamation marks

# Some default parameters for the gst queues. These can be overridden by the application configuration.
QueueParams = collections.namedtuple("QueueParams", "max_buffers max_bytes max_time leaky")
QUEUE_PARAMS = QueueParams(max_buffers=3, max_bytes=0, max_time=0, leaky='no')

class Element:
    """
    A Python wrapper around a GStreamer element.

    Each `Element` class should define an `element_pipeline` property,
    which is a string that can be used in a parse and launch call.
    """
    def __init__(self, name: str) -> None:
        self.name = name
        self.element_pipeline = None

class GStreamerSource(Element):
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
        super().__init__(name)
        self.source_uri = source_uri
        self.video_format = video_format
        self.video_width = video_width
        self.video_height = video_height

        if os.path.exists(source_uri):
            # Source is a file (note that this will have to be updated if we ever support devices found in /dev/*)
            source_element = (
                f'filesrc location="{source_uri}" name={name} ! '
                f'queue name={name}_queue_dec264 leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
                f'qtdemux ! '
                f'h264parse ! '
                f'avdec_h264 max-threads=2'
            )
        elif source_uri == "cam0" or source_uri == "cam1":
            # Source is CSI camera interface
             source_element = (
                f'libcamerasrc name={name} ! '
                f'video/x-raw, format={video_format}, width={video_width}, height={video_height}'
            )
        else:
            # RTSP camera or something. Not currently supported.
            raise ValueError(f"Given a source_uri that is not supported: {source_uri}")

        # TODO: Remove elements here that we don't need/want. E.g., the videoscale and videoconvert portions don't seem to do anything. Verify and remove them.
        self.element_pipeline = (
            f'{source_element} ! '
            f'queue name={name}_queue_scale leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
            f'videoscale name={name}_videoscale n-threads=2 ! '
            f'queue name={name}_queue_convert leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
            f'videoconvert n-threads=3 name={name}_convert qos=false ! '
            f'video/x-raw, format={video_format}, pixel-aspect-ratio=1/1 '
        )

class GStreamerPreprocess(Element):
    def __init__(self, so_fpath: str, name="pre-process") -> None:
        super().__init__(name)
        raise NotImplementedError()

class GStreamerModel(Element):
    def __init__(self, hef_fpath: str, batch_size: int, name="model") -> None:
        super().__init__(name)
        self.hef_fpath = hef_fpath
        self.batch_size = batch_size

        batch_size = str(batch_size)

        if not os.path.isfile(self.hef_fpath):
            raise FileNotFoundError(f"Cannot find the given hef file: {hef_fpath}")

        self.element_pipeline = (
            # Wrapper (pre-)
            f'queue name=wrapper_queue_input leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
            f'hailocropper name=wrapper_crop so-path={whole_buffer_crop_so} function-name=create_crops use-letterbox=true resize-method=inter-area internal-offset=true '
            f'hailoaggregator name=wrapper_agg '
            ## Wrapper Aggregator Sink 0 path
            f'wrapper_crop. ! '
            f'queue name=wrapper_queue_bypass leaky={QUEUE_PARAMS.leaky} max-size-buffers={bypass_max_size_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
            f'wrapper_agg.sink_0 '
            ## Wrapper Aggregator Sink 1 path (wraps the inference portion)
            f'wrapper_crop. ! '

            # Inference proper
            f'queue name={name}_queue_scale leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
            f'videoscale name={name}_videoscale n-threads=2 qos=false ! '
            f'queue name={name}_queue_aspect leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
            f'video/x-raw, pixel-aspect-ratio=1/1 ! '
            f'videoconvert name={name}_videoconvert n-threads=2 ! '
            f'queue name={name}_queue_hailo leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
            f'hailonet name={name}_hailonet hef-path={hef_fpath} batch-size={batch_size} {additional_params} force-writable=true '
        )
    
class GStreamerHailoPostprocess(Element):
    def __init__(self, so_fpath: str, function_name: str, config_fpath=None, name="ai-post-process") -> None:
        super().__init__(name)
        self.so_fpath = so_fpath
        self.function_name = function_name
        self.config_fpath = config_fpath

        if not os.path.isfile(so_fpath):
            raise FileNotFoundError(f"Cannot find the given .so file: {so_fpath}")

        if config_fpath is not None and not os.path.isfile(config_fpath):
            raise FileNotFoundError(f"Cannot find the given configuration file: {config_fpath}")

        config_str = "" if self.config_fpath is None else f"config-path={self.config_fpath}"

        self.element_pipeline = (
            f'queue name={name}_queue_filter leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
            f'hailofilter name={name}_hailofilter so-path={self.so_fpath} {config_str} function-name={self.function_name} qos=false ! '

            # Wrapper (post-)
            ## Aggregator Sink 1 end
            f'wrapper_agg.sink_1 '
            ## Both paths now meet up here
            f'wrapper_agg. ! '
            f'queue name={name}_queue_postproc_output leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} '
        )

class GStreamerCustomPostprocess(Element):
    def __init__(self, name="post-process") -> None:
        super().__init__(name)
        raise NotImplementedError()

class GStreamerSink(Element):
    def __init__(self, sink_uris: List[str]|str, name="sink") -> None:
        """
        Accepts a list of sink URIs or a single one.

        URIs should be endpoints. Either RTSP endpoints such as "rtsp://192.168.1.1:5000",
        file paths such as "/path/to/out.h264",
        or "display", in which case the screen is used.
        """
        super().__init__(name)
        if issubclass(type(sink_uris), str):
            # Only one item
            sink_uris = [sink_uris]

        self.element_pipeline = (
            f'queue name={name}_queue_hailooverlay" leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
            f'hailooverlay name={name}_hailooverlay ! '
            f'queue name={name}_queue_videoconvert leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
            f'videoconvert name={name}_videoconvert n-threads=2 qos=false ! '
            f'queue name={name}_display_queue leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
        )

        for i, uri in enumerate(sink_uris):
            if i == 0 and len(sink_uris) > 1:
                self.element_pipeline += f'tee name={name}_tee ! '
                self.element_pipeline += f'queue name={name}_tee_queue{i} leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '
            elif len(sink_uris) > 1:
                self.element_pipeline += f' ! '
                self.element_pipeline += f'{name}_tee. ! '
                self.element_pipeline += f'queue name={name}_tee_queue{i} leaky={QUEUE_PARAMS.leaky} max-size-buffers={QUEUE_PARAMS.max_buffers} max-size-bytes={QUEUE_PARAMS.max_bytes} max-size-time={QUEUE_PARAMS.max_time} ! '

            if uri.startswith("http") or uri.startswith("rtsp"):
                # Treat as an RTSP endpoint
                uri_parse = urllib.parse.urlparse(uri)
                ip_or_url, port = uri_parse.netloc.split(':')
                # TODO: Set the host and port on the udpsink
                # TODO: Handle encryption
                self.element_pipeline += f'ffenc_h264 ! '
                self.element_pipeline += f'video/x-h264 ! '
                self.element_pipeline += f'rtph264ppay ! '
                self.element_pipeline += f'fpsdisplaysink name={name}_udpsink_with_fps video-sink=udpsink sync=true text-overlay=true signal-fps-measurements=true'
            elif uri == "display":
                # Display to screen
                self.element_pipeline += f'fpsdisplaysink name={name}_xvimagesink_with_fps video-sink=xvimagesink sync=true text-overlay=true signal-fps-measurements=true'
            else:
                # Treat as a filesink
                # TODO: Figure out how to tell the filesink what file to use
                self.element_pipeline += f'fpsdisplaysink name={name}_filesink_with_fps video-sink=filesink sync=true text-overlay=true signal-fps-measurements=true'

class GStreamerApp:
    def __init__(self, name: str, *elements) -> None:
        self.name = name
        self.elements = [e for e in elements if e is not None]
        self.repeat_on_end_of_stream = False

        # Create the pipeline
        Gst.init(None)
        pipeline_string = " ! ".join([e.element_pipeline for e in self.elements if e.element_pipeline is not None])
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

        # Disable QoS to prevent frame drops
        disable_qos(self.pipeline)

        # Set pipeline to PLAYING state
        self.pipeline.set_state(Gst.State.PLAYING)

        # Run the GLib event loop
        self.loop.run()

        # Clean up
        self.pipeline.set_state(Gst.State.NULL)

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

    def rewind(self):
        """
        Attempt to rewind the pipeline to the beginning.
        """
        if self.pipeline.get_state() == Gst.State.PLAYING:
            self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, 0)

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

def disable_qos(pipeline):
    """
    Iterate through all elements in the given GStreamer pipeline and set the qos property to False
    where applicable.
    When the 'qos' property is set to True, the element will measure the time it takes to process each
    buffer and will drop frames if latency is too high.
    We are running on long pipelines, so we want to disable this feature to avoid dropping frames.
    
    This function is taken almost completely from HAILO examples repo.
    """
    # Iterate through all elements in the pipeline
    it = pipeline.iterate_elements()
    while True:
        result, element = it.next()
        if result != Gst.IteratorResult.OK:
            break

        # Check if the element has the 'qos' property
        if 'qos' in GObject.list_properties(element):
            # Set the 'qos' property to False
            element.set_property('qos', False)
            log.debug(f"Set qos to False for {element.get_name()}")

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
