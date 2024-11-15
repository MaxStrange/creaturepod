from . import element
from . import model

class GStreamerHailoPreprocess(element.Element):
    def __init__(self, model_config: model.AIModelConfiguration, name="ai-pre-process") -> None:
        super().__init__(name)

        # Currently nothing to do
        self.element_pipeline = ""

class GStreamerPreprocess(element.Element):
    def __init__(self, so_fpath: str, name="pre-process") -> None:
        super().__init__(name)
        raise NotImplementedError()
