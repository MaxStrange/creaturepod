import os
from . import element
from . import utils

class GStreamerSource(element.Element):
    """
    A class to encapsulate a GStreamer source that can be added into a pipeline.
    """
    def __init__(self, source_uri: str, video_format="RGB", video_width=640, video_height=640, desired_video_format="RGB", desired_video_width=640, desired_video_height=640, name="source") -> None:
        """
        Create an instance of a GStreamerSource that can be added to a pipeline.

        Note that the arguments supplied to this function should be the ones that come out of the
        source - not the desired ones. If you want to scale or otherwise adjust the video frames
        after retrieving them from the source, you should do that in a preprocess element.

        Args
        ----
        - `source_uri`: (`str`) The URI for the source of video. A camera ID like 'cam0' as found
           in the appconfig YAML file will be treated as a Raspberry Pi camera module coming over the
           corresponding (0 or 1) CSI port. A string like 'rtsp:5000' will be treated as a udpsource running on
           port 5000 that expects an RTSP stream.
        - `video_format`: (`str`) The format of the video. See the GStreamer pad documentation for your source.
        - `video_width`: (`int`) The width (in pixels) of the video.
        - `video_height`: (`int`) The height (in pixels) of the video.
        - `desired_video_format`: (`str`) The desired format of the video. We convert to this if it is different from the source.
        - `desired_video_width`: (`int`) The width (in pixels) desired. We convert to this if it is different from the source.
        - `desired_video_height`: (`int`) The height (in pixels) desired. We convert to this if it is different from the source.
        - `name`: (`str`) The name of the source element for debugging.
        """
        super().__init__(name)
        self.source_uri = source_uri
        self.video_format = video_format
        self.video_width = video_width
        self.video_height = video_height
        self.desired_video_format = desired_video_format
        self.desired_video_width = desired_video_width
        self.desired_video_height = desired_video_height

        # TODO: Need to determine how best to decide what demuxer to use after the filesrc
        if os.path.exists(source_uri) and os.path.splitext(source_uri)[-1].lower() == ".mov":
            # QuickTime style
            source_element = (
                # Grab frames from the file
                f'filesrc location="{source_uri}" name={name} ! '
                # Demux the sound and the video
                f'qtdemux name={name}_qtdemux '

                # Audio is currently handled in a fairly naive manner
                f'{name}_qtdemux.audio_0 ! queue ! decodebin ! audioconvert ! vorbisenc ! audioresample name="source_audio_channel" '

                # Video portion of the pipeline:
                f'{name}_qtdemux.video_0 ! '
                # Push frames into a queue. This means the filesrc and demuxer are running in their own thread, while a new thread is used
                # for the next block (up to the next queue)
                f'queue name={name}_queue_dec264 leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
                # Parse the incoming H.264 stream (inputs video/x-h264 and outputs video/x-h264 that has appropriate alignment and formatting for downstream elements)
                f'h264parse ! '
                # Decode H.264 stream (inputs video/x-h264 and outputs video/x-raw).
                # TODO There are several arguments here that can be tuned. Check them if need be.
                f'avdec_h264 max-threads=2'
            )
        elif os.path.exists(source_uri):
            # Assume we have an h.264 raw video
            source_element = (
                # Grab frames from the file
                f'filesrc location="{source_uri}" name={name} ! '
                # Push frames into a queue. This means the filesrc and demuxer are running in their own thread, while a new thread is used
                # for the next block (up to the next queue)
                f'queue name={name}_queue_dec264 leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
                # Parse the incoming H.264 stream (inputs video/x-h264 and outputs video/x-h264 that has appropriate alignment and formatting for downstream elements)
                f'h264parse ! '
                # Decode H.264 stream (inputs video/x-h264 and outputs video/x-raw).
                # TODO There are several arguments here that can be tuned. Check them if need be.
                f'avdec_h264 max-threads=2'
            )
        elif source_uri == "cam0" or source_uri == "cam1" or "imx219" in source_uri:  # TODO
            # Source is CSI camera interface
             source_element = (
                # First, pull the audio stream and convert to vorbis encoding
# TODO: Audio
#                f'alsasrc ! queue ! audioconvert ! vorbisenc ! audioresample name="source_audio_channel" '

                # Pull camera data from the Raspberry Pi camera device.
                # Note that this element is not part of a normal GStreamer installation
                # and is not documented as part of GStreamer. The element is provided as part of libcamera.
                f'libcamerasrc name={name} camera-name={source_uri} ! video/x-raw, format={video_format}, width={video_width}, height={video_height} '
            )
        else:
            # RTSP stream
            # TODO: Handle decryption/authentication
            schema, port = source_uri.split(':')
            source_element = (
                # Pull data from UDP on the given port.
                # TODO: There is a good chance you will have to muck around with the caps on this element
                # since the caps are left undetermined (they should be delivered out of band by SDP)
                # TODO: Look into rtspsrc instead
                # TODO: Need to add audio
                f'udpsrc port={port} ! application/x-rtp,clock-rate=90000,payload=96 ! '
                # Interpret the UDP source as RTP packets and extract H.264 video from them
                f'rtph264pdepay queue-delay=0 ! '
                # Decode H.264 to x-raw
                f'avdec_h264 max-threads=2'
            )

        self.element_pipeline = (
            # Source element (from above)
            f'{source_element} ! '
            # Scale the video to whatever we need (as determined downstream)
            f'queue name={name}_queue_scale leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
            f'videoscale name={name}_videoscale n-threads=2 ! video/x-raw, width={self.desired_video_width}, height={self.desired_video_height} ! '
            # Convert the video to whatever video format
            f'queue name={name}_queue_convert leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
            f'videoconvert n-threads=3 name={name}_convert qos=false ! video/x-raw, format={self.desired_video_format}, pixel-aspect-ratio=1/1 '
        )
