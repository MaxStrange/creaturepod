from typing import Any
from typing import Dict
from . import element
from . import model

class GStreamerHailoPreprocess(element.Element):
    def __init__(self, model_config: Dict[str, Any], name="ai-pre-process") -> None:
        super().__init__(name)

    @property
    def element_pipeline(self) -> str:
        """
        The string representation of this element. 
        """
        return ""

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
