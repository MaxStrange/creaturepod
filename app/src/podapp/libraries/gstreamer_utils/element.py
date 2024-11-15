class Element:
    """
    A Python wrapper around a GStreamer element.

    Each `Element` class should define an `element_pipeline` property,
    which is a string that can be used in a parse and launch call.
    """
    def __init__(self, name: str) -> None:
        self.name = name
        self.element_pipeline = None
