from typing import Any
from typing import Dict
from . import element
from . import model

class GStreamerHailoPreprocess(element.Element):
    def __init__(self, model_config: Dict[str, Any], name="ai-pre-process") -> None:
        super().__init__(name)
        self.video_width = model_config.get('width', None)
        self.video_height = model_config.get('height', None)
        self.video_format = model_config.get('color_format', None)

    @property
    def element_pipeline(self) -> str:
        """
        The string representation of this element. 
        """
        element_pipeline = ""

        if self.video_format is not None:
            element_pipeline += f"videoconvert ! video/x-raw, format={self.video_format} "

        if self.video_height is not None or self.video_width is not None:
            if element_pipeline:
                element_pipeline += " ! "
            element_pipeline += f"videoscale ! video/x-raw, "
            if self.video_height is not None:
                element_pipeline += f"height={self.video_height}, "
            if self.video_width is not None:
                element_pipeline += f"width={self.video_width}, "
            element_pipeline = element_pipeline.rstrip().removesuffix(',') + " "

        return element_pipeline

class GStreamerPreprocess(element.Element):
    def __init__(self, so_fpath: str, name="pre-process") -> None:
        super().__init__(name)
        raise NotImplementedError()

    @property
    def element_pipeline(self) -> str:
        """
        The string representation of this element. 
        """
        return ""
