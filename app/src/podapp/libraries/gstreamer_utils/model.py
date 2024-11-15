import dataclasses
import os
from . import element
from . import utils

@dataclasses.dataclass
class AIModelConfiguration:
    """
    Subclasses of this class should contain all the data needed for configuring
    a particular AI model.
    """
    # Batch size
    batch_size: int

    # Width of input (or maybe the output?)
    width: int

    # Height of input (or maybe the output?)
    height: int

    # Color format (RGB, etc.)
    color_format: str

    # Model .hef file name. File should be located in folder specified by appconfig['moduleconfig']['gstreamer-utils']['hailo']['base-model-folder-path']
    hef_name: str

    # Post-processing shared object file name.
    post_process_so_name: str

    # Post-processing function name
    post_process_so_function: str = "filter"

    # Output format type
    output_format_type: str

@dataclasses.dataclass
class ObjectDetectionYoloV8(AIModelConfiguration):
    """
    Configuration for an object detection model,
    specifically YOLOv8.
    """
    batch_size = 2
    width = 640
    height = 640
    color_format = "RGB"
    hef_name = "yolov8s_h8l.hef"
    post_process_so_name = "libyolo_hailortpp_postprocess.so"
    output_format_type = "HAILO_FORMAT_TYPE_FLOAT32"

    # Non-maximal suppression score threshold
    nms_score_threshold: float = 0.3

    # Non-maximal suppression intersection over union threshold
    nms_iou_threshold: float = 0.45

@dataclasses.dataclass
class InstanceSegmentation(AIModelConfiguration):
    """
    Configuration for an instance segmentation model.
    """
    batch_size = 2
    width = 640
    height = 640
    color_format = "RGB"
    hef_name = "yolov5n_seg_h8l_mz.hef"
    post_process_so_name = "libyolov5seg_postprocess.so"
    post_process_so_function = "yolov5seg"

    # This model has a config file
    config_file_name = "yolov5n_seg.json"

@dataclasses.dataclass
class PoseEstimation(AIModelConfiguration):
    """
    Configuration for a pose estimation model.
    """
    batch_size = 2
    width = 640
    height = 640
    color_format = "RGB"
    hef_name = "yolov8s_pose_h8l.hef"
    post_process_so_name = "libyolov8pose_postprocess.so"

class GStreamerModel(element.Element):
    def __init__(self, model_config: AIModelConfiguration, name="model") -> None:
        super().__init__(name)
        self.hef_fpath = os.path.join(utils.HailoParams.base_model_folder_path, model_config.hef_name)
        self.batch_size = batch_size

        batch_size = str(batch_size)

        if not os.path.isfile(self.hef_fpath):
            raise FileNotFoundError(f"Cannot find the given hef file: {self.hef_fpath}")

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
            f'hailonet name={name}_hailonet hef-path={self.hef_fpath} batch-size={batch_size} force-writable=true '
        )
 