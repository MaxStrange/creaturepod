import os
from . import element
from . import utils

class GStreamerSource(element.Element):
    """
    A class to encapsulate a GStreamer source that can be added into a pipeline.
    """
    def __init__(self, source_uri: str, video_format="RGB", video_width=640, video_height=640, name="source") -> None:
        """
        Create an instance of a GStreamerSource that can be added to a pipeline.

        Args
        ----
        - `source_uri`: (`str`) The URI for the source of video. A camera ID like 'cam0' as found
           in the appconfig YAML file will be treated as a Raspberry Pi camera module coming over the
           corresponding (0 or 1) CSI port. A string like 'rtsp:5000' will be treated as a udpsource running on
           port 5000 that expects an RTSP stream.
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

    @property
    def element_pipeline(self) -> str:
        """
        The string representation of this element.
        """
        # Determine if there is audio to deal with
        src_is_file = os.path.exists(self.source_uri)
        if src_is_file:
            _, extension = os.path.splitext(self.source_uri)
            extension = extension.lower()
            if extension == ".mov":
                # Quicktime format. There is audio in this file.
                audio_present = True
            else:
                # Assume no audio.
                audio_present = False

        if src_is_file and audio_present:
            source_element = (
                # Grab frames from the file
                f'filesrc location="{self.source_uri}" name={self.name} ! '
                # Demux the sound and the video
                f'qtdemux name={self.name}_qtdemux '

                # Audio portion of pipeline
                # TODO: We don't really do anything with the audio yet.
                f'{self.name}_qtdemux.audio_0 ! queue ! decodebin ! audioconvert ! vorbisenc ! audioresample name="{self.name}_audio_channel" ! fakeaudiosink '

                # Video portion of the pipeline:
                f'{self.name}_qtdemux.video_0 ! '
                # Push frames into a queue. This means the filesrc and demuxer are running in their own thread, while a new thread is used
                # for the next block (up to the next queue)
                f'queue name={self.name}_queue_dec264 leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
                # Parse the incoming H.264 stream (inputs video/x-h264 and outputs video/x-h264 that has appropriate alignment and formatting for downstream elements)
                f'h264parse ! '
                # Decode H.264 stream (inputs video/x-h264 and outputs video/x-raw).
                f'avdec_h264 max-threads=2 '
            )
        elif src_is_file and not audio_present:
            source_element = (
                # Grab frames from the file
                f'filesrc location="{self.source_uri}" name={self.name} ! '
                # Push frames into a queue. This means the filesrc and demuxer are running in their own thread, while a new thread is used
                # for the next block (up to the next queue)
                f'queue name={self.name}_queue_dec264 leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
                # Parse the incoming H.264 stream (inputs video/x-h264 and outputs video/x-h264 that has appropriate alignment and formatting for downstream elements)
                f'h264parse ! '
                # Decode H.264 stream (inputs video/x-h264 and outputs video/x-raw).
                f'avdec_h264 max-threads=2 '
            )
        elif self.source_uri.startswith("http") or self.source_uri.startswith("rtsp"):
            # RTSP stream
            # TODO: Handle decryption/authentication
            schema, port = self.source_uri.split(':')
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
                f'avdec_h264 max-threads=2 '
            )
        else:
            # Source is CSI camera interface
            source_element = (
                # Pull camera data from the Raspberry Pi camera device.
                # Note that this element is not part of a normal GStreamer installation
                # and is not documented as part of GStreamer. The element is provided as part of libcamera.
                f'libcamerasrc name={self.name} camera-name={self.source_uri} ! '
                f'video/x-raw, format={self.video_format}, width={self.video_width}, height={self.video_height} '
            )

        element_pipeline = (
            # Source element (from above)
            f'{source_element}'
        )

        return element_pipeline
