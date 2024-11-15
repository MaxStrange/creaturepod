from . import element

class GStreamerPreprocess(element.Element):
    def __init__(self, so_fpath: str, name="pre-process") -> None:
        super().__init__(name)
        raise NotImplementedError()
