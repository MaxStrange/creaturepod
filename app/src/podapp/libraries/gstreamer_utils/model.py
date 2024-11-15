import os
from . import element
from . import utils

class GStreamerModel(element.Element):
    def __init__(self, hef_fpath: str, batch_size: int, name="model") -> None:
        super().__init__(name)
        self.hef_fpath = hef_fpath
        self.batch_size = batch_size

        batch_size = str(batch_size)

        if not os.path.isfile(self.hef_fpath):
            raise FileNotFoundError(f"Cannot find the given hef file: {hef_fpath}")

        self.element_pipeline = (
            # Wrapper (pre-). This portion of the pipeline is important for the HAILO stuff to add an overlay. It is not technically needed for inference.
            ## https://github.com/hailo-ai/tappas/blob/master/docs/elements/hailo_cropper.rst
            ## The cropper outputs unmodified frames on one pad and cropped frames on another.
            f'queue name=wrapper_queue_input leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
            f'hailocropper name=wrapper_crop so-path={utils.HAILO_PARAMS.cropping_so_path} function-name=create_crops use-letterbox=true resize-method=inter-area internal-offset=true '

            ## https://github.com/hailo-ai/tappas/blob/master/docs/elements/hailo_aggregator.rst
            ## The aggregator takes unmodified frames on one pad and inference overlays on another.
            f'hailoaggregator name=wrapper_agg '
            ## Wrapper Aggregator Sink 0 path
            f'wrapper_crop. ! '
            f'queue name=wrapper_queue_bypass leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
            f'wrapper_agg.sink_0 '

            ## Wrapper Aggregator Sink 1 path (wraps the inference portion)
            f'wrapper_crop. ! '
            # Inference proper
            ## Scale the video to whatever is required by the neural network
            f'queue name={name}_queue_scale leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
            f'videoscale name={name}_videoscale n-threads=2 qos=false ! '
            ## Convert the video to whatever format is required by the neural network
            f'queue name={name}_queue_aspect leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
            f'videoconvert name={name}_videoconvert n-threads=2 ! video/x-raw, pixel-aspect-ratio=1/1 ! '
            ## Feed into the neural network (which will run on the coprocessor); TODO: Make sure to use gst inspect on the Hailo elements to determine property options
            f'queue name={name}_queue_hailo leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
            f'hailonet name={name}_hailonet hef-path={hef_fpath} batch-size={batch_size} force-writable=true '
        )
 