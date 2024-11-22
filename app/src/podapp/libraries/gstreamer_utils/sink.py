import urllib
from typing import List
from . import element
from . import utils

class GStreamerSink(element.Element):
    def __init__(self, sink_uris: List[str]|str, overlay=False, name="sink") -> None:
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

        self.sink_uris = sink_uris
        self.overlay = overlay

    @property
    def element_pipeline(self) -> str:
        """
        The string representation of this element. 
        """
        element_pipeline = ""
        if self.overlay:
            self.element_pipeline += (
                # Draw overlays
                f'queue name={self.name}_queue_hailooverlay" leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
                f'hailooverlay name={self.name}_hailooverlay ! '
            )

        self.element_pipeline += (
            # Convert to downstream sink format
            f'queue name={self.name}_queue_videoconvert leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
            f'videoconvert name={self.name}_videoconvert n-threads=2 qos=false ! '

            # Sink queue
            f'queue name={self.name}_sink_queue leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
        )

        for i, uri in enumerate(self.sink_uris):
            if i == 0 and len(self.sink_uris) > 1:
                self.element_pipeline += f'tee name={self.name}_tee ! '
                self.element_pipeline += f'queue name={self.name}_tee_queue{i} leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
            elif len(self.sink_uris) > 1:
                self.element_pipeline += f' ! '
                self.element_pipeline += f'{self.name}_tee. ! '
                self.element_pipeline += f'queue name={self.name}_tee_queue{i} leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '

            if uri.startswith("http") or uri.startswith("rtsp"):
                # Treat as an RTSP endpoint
                uri_parse = urllib.parse.urlparse(uri)
                ip_or_url, port = uri_parse.netloc.split(':')
                # TODO: Set the host and port on the udpsink
                # TODO: Handle encryption
                self.element_pipeline += f'ffenc_h264 ! video/x-h264 ! '
                self.element_pipeline += f'rtph264ppay ! '
                self.element_pipeline += f'udpsink'  # TODO
            elif uri == "display":
                # Display to screen
                self.element_pipeline += f'fpsdisplaysink name={self.name}_xvimagesink_with_fps video-sink=xvimagesink sync=true text-overlay=true signal-fps-measurements=true'
            else:
                # Treat as a filesink
                self.element_pipeline += f'filesink name={self.name}_filesink location={uri}'

        return element_pipeline
