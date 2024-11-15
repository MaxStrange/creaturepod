import os
from . import element
from . import utils

class GStreamerHailoPostprocess(element.Element):
    def __init__(self, so_fpath: str, function_name: str, config_fpath=None, name="ai-post-process") -> None:
        super().__init__(name)
        self.so_fpath = so_fpath
        self.function_name = function_name
        self.config_fpath = config_fpath

        if not os.path.isfile(so_fpath):
            raise FileNotFoundError(f"Cannot find the given .so file: {so_fpath}")

        if config_fpath is not None and not os.path.isfile(config_fpath):
            raise FileNotFoundError(f"Cannot find the given configuration file: {config_fpath}")

        config_str = "" if self.config_fpath is None else f"config-path={self.config_fpath}"

        self.element_pipeline = (
            ## Filter: https://github.com/hailo-ai/tappas/blob/master/docs/elements/hailo_filter.rst
            f'queue name={name}_queue_filter leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} ! '
            f'hailofilter name={name}_hailofilter so-path={self.so_fpath} {config_str} function-name={self.function_name} qos=false ! '

            # Wrapper (post-)
            ## Aggregator Sink 1 end ; TODO: Check the docs to make sure I understand this syntax
            f'wrapper_agg.sink_1 '
            ## Both paths now meet up here
            f'wrapper_agg. ! '
            f'queue name={name}_queue_postproc_output leaky={utils.QUEUE_PARAMS.leaky} max-size-buffers={utils.QUEUE_PARAMS.max_buffers} max-size-bytes={utils.QUEUE_PARAMS.max_bytes} max-size-time={utils.QUEUE_PARAMS.max_time} '
        )

class GStreamerCustomPostprocess(element.Element):
    def __init__(self, name="post-process") -> None:
        super().__init__(name)
        raise NotImplementedError()
