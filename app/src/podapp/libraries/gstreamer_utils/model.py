import os
from typing import Any
from typing import Dict
from . import element
from . import utils

# Default values for AI Model Configurations
DEFAULT_AI_MODEL_CONFIGURATION = {
    # Batch size
    "batch_size": 2,
    # Width of input (or maybe the output?)  # TODO: Double check the resolution of output video to confirm whether this is input or output
    "width": 640,
    # Height of input (or maybe the output?)
    "height": 640,
    # Color format (RGB, etc.)
    "color_format": "RGB",
    # Post-processing function name
    "post_process_so_function": "filter",

    # Model .hef file name. File should be located in folder specified by appconfig['moduleconfig']['gstreamer-utils']['hailo']['base-model-folder-path']
    "hef_name": "",
    # Post-processing shared object file name.
    "post_process_so_name": "",
    # Output format type
    "output_format_type": "",
}

# Values for object detection with YOLOv8
OBJECT_DETECTION_YOLOV8 = DEFAULT_AI_MODEL_CONFIGURATION | {
    "hef_name": "yolov8s_h8l.hef",
    "post_process_so_name": "libyolo_hailortpp_postprocess.so",
    "output_format_type": "HAILO_FORMAT_TYPE_FLOAT32",
    "width": 1536,
    "height": 864,

    # Non-maximal suppression score threshold
    "nms_score_threshold": 0.3,
    # Non-maximal suppression intersection over union threshold
    "nms_iou_threshold": 0.45,
}

# Values for instance segmentation
INSTANCE_SEGMENTATION = DEFAULT_AI_MODEL_CONFIGURATION | {
    "hef_name": "yolov5n_seg_h8l_mz.hef",
    "post_process_so_name": "libyolov5seg_postprocess.so",
    "post_process_so_function": "yolov5seg",

    # This model has a config file
    "config_file_name": "yolov5n_seg.json",
}

# Values for pose estimation
POSE_ESTIMATION = DEFAULT_AI_MODEL_CONFIGURATION | {
    "hef_name": "yolov8s_pose_h8l.hef",
    "post_process_so_name": "libyolov8pose_postprocess.so",
}

# TODO: When/if we need a model cascade, make sure too look at hailocropper. Cropping folder path is stored in the HAILO PARAMS.

class GStreamerModel(element.Element):
    def __init__(self, model_config: Dict[str, Any], name="model") -> None:
        super().__init__(name)
        self.hef_fpath = os.path.join(utils.HAILO_PARAMS.base_model_folder_path, model_config['hef_name'])
        self.batch_size = model_config['batch_size']

        if not os.path.isfile(self.hef_fpath):
            raise FileNotFoundError(f"Cannot find the given hef file: {self.hef_fpath}")

    @property
    def element_pipeline(self) -> str:
        """
        The string representation of this element.
        """
        element_pipeline = (
            # Scale the video to whatever is required by the neural network
            f'queue name={self.name}_queue_scale leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
            f'videoscale name={self.name}_videoscale n-threads=2 qos=false ! '
            # Convert the video to whatever format is required by the neural network
            f'queue name={self.name}_queue_aspect leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
            f'video/x-raw, pixel-aspect-ratio=1/1 ! '
            f'videoconvert name={self.name}_videoconvert n-threads=2 ! '
            # Feed into the neural network (which will run on the coprocessor)
            f'queue name={self.name}_queue_hailo leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
            f'hailonet name={self.name}_hailonet hef-path={self.hef_fpath} batch-size={self.batch_size} force-writable=true '
        )
 
        return element_pipeline
