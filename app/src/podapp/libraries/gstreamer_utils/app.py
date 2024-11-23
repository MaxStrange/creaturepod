import os
import threading
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GLib
from gi.repository import Gst
from ..common import log
from . import utils

# TODO: Think over how to make this asynchronous. It's kind of hacked together

class GStreamerApp:
    def __init__(self, name: str, *elements) -> None:
        self.name = name
        self.elements = [e for e in elements if e is not None]
        self.repeat_on_end_of_stream = False

        # Create the pipeline
        Gst.init(None)
        pipeline_string = " ! ".join([e.element_pipeline for e in self.elements if e.element_pipeline])
        log.debug(f"Parse-Launching: {pipeline_string}")
        ######################
        # TODO : REMOVE ME
        print(pipeline_string)
        ######################
        self.pipeline = Gst.parse_launch(pipeline_string)

        # Save dot file (if desired)
        log.debug(f"Checking for GST_DEBUG_DUMP_DOT_DIR in environment.")
        if os.environ.get("GST_DEBUG_DUMP_DOT_DIR", None) is not None:
            path = os.environ.get("GST_DEBUG_DUMP_DOT_DIR")
            log.debug(f"Writing dot files to: {path}")
            Gst.debug_bin_to_dot_file(self.pipeline, Gst.DebugGraphDetails.ALL, self.name)

        # Create the mainloop
        self.loop = GLib.MainLoop()
        self.loop_thread = None

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
                log.warning(f"Quality of service message received from pipeline {self.name}, element {qos_element}. Message: {message}")
                return True
            case Gst.MessageType.STREAM_STATUS:
                # A change in the stream status
                status, owner = message.parse_stream_status()
                log.info(f"Stream status changed in pipeline {self.name}: {status}. Owner: {owner}")
                return True
            case Gst.MessageType.ELEMENT:
                # Element-specific bus message. Potentially could want a handler.
                # TODO: Add element-wise handlers?
                log.info(f"Pipeline {self.name} received an element-specific message from {message.src.get_name()}: {message}")
                return True
            case _:
                # There are a ton of possible message types. Mostly just ignore them and pretend like we handled them.
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
        utils.disable_qos(self.pipeline)

        # Set pipeline to PLAYING state
        self.pipeline.set_state(Gst.State.PLAYING)

        # Run the GLib event loop
        self.loop_thread = threading.Thread(target=self.loop.run)
        self.loop_thread.start()

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

        if self.loop_thread is not None:
            self.loop_thread.join()

    def rewind(self):
        """
        Attempt to rewind the pipeline to the beginning.
        """
        timeout_s = 3
        state = self.pipeline.get_state(timeout_s * Gst.SECOND)
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!! STATE:", state)
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        if state == Gst.State.PLAYING:
            self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, 0)
