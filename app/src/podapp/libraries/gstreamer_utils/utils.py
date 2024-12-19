import collections
import os
import urllib
import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject
from gi.repository import Gst
from ..common import log
from typing import Any
from typing import Dict

# Some default parameters for the gst queues. These can be overridden by the application configuration.
QueueParams = collections.namedtuple("QueueParams", "max_buffers max_bytes max_time leaky")
QUEUE_PARAMS = QueueParams(max_buffers=3, max_bytes=0, max_time=0, leaky='no')

# Some default parameters for the HAILO-specific elements. These can be overridden by the application configuration.
HailoParams = collections.namedtuple("HailoParams", "cropping_algorithm_folder_path base_model_folder_path post_process_folder_path")
HAILO_PARAMS = HailoParams(cropping_algorithm_folder_path="UNINITIALIZED", base_model_folder_path="UNINITIALIZED", post_process_folder_path="UNINITIALIZED")


def configure(config: Dict[str, Any]):
    """
    Configure the gstreamer utils.
    """
    if 'gstreamer-utils' not in config['moduleconfig']:
        return

    gstreamer_config = config['moduleconfig']['gstreamer-utils']

    # Queue params
    global QUEUE_PARAMS
    if 'queue-params' in gstreamer_config:
        leaky = gstreamer_config['queue-params'].get('leaky', QUEUE_PARAMS.leaky)
        max_buffers = gstreamer_config['queue-params'].get('max-buffers', QUEUE_PARAMS.max_buffers)
        max_bytes = gstreamer_config['queue-params'].get('max-bytes', QUEUE_PARAMS.max_bytes)
        max_time = gstreamer_config['queue-params'].get('max-time', QUEUE_PARAMS.max_time)
        QUEUE_PARAMS = QueueParams(leaky=leaky, max_buffers=max_buffers, max_bytes=max_bytes, max_time=max_time)

    # Dot graph (the GStreamer pipeline can print itself to a dot file)
    if 'dot-graph' in gstreamer_config and gstreamer_config['dot-graph']['save']:
        dpath = gstreamer_config['dot-graph']['dpath']
        if os.path.isdir(dpath):
            log.debug(f"Will save DOT files to directory: {dpath}")
            os.environ["GST_DEBUG_DUMP_DOT_DIR"] = dpath
        else:
            log.warning(f"Config file's moduleconfig->gstreamer-utils->dot-graph->dpath does not point to a directory. Given {dpath}")

    # HAILO-specific stuff
    global HAILO_PARAMS
    if 'hailo' in gstreamer_config:
        hailo_config = gstreamer_config['hailo']
        cropping_algorithm_folder_path = hailo_config['cropping-algorithm-folder-path']
        base_model_folder_path = hailo_config['base-model-folder-path']
        post_process_folder_path = hailo_config['post-process-folder-path']

        HAILO_PARAMS = HailoParams(cropping_algorithm_folder_path=cropping_algorithm_folder_path, base_model_folder_path=base_model_folder_path, post_process_folder_path=post_process_folder_path)

    # GStreamer has separate logging parameters
    if 'logging' in gstreamer_config:
        log_level = gstreamer_config['logging']['level']
        match log_level.upper():
            case "NONE":
                os.environ['GST_DEBUG'] = "0"
            case "ERROR":
                os.environ['GST_DEBUG'] = "1"
            case "WARNING":
                os.environ['GST_DEBUG'] = "2"
            case "FIXME":
                os.environ['GST_DEBUG'] = "3"
            case "INFO":
                os.environ['GST_DEBUG'] = "4"
            case "DEBUG":
                os.environ['GST_DEBUG'] = "5"
            case "LOG":
                os.environ['GST_DEBUG'] = "6"
            case "TRACE":
                os.environ['GST_DEBUG'] = "7"
            case "MEMDUMP":
                os.environ['GST_DEBUG'] = "9"  # No 8 for some reason
            case _:
                log.warning(f"Unrecognized log level for GST: '{log_level}'. Defaulting to 'WARNING'")
                os.environ['GST_DEBUG'] = "2"  # Default to warning

def disable_qos(pipeline):
    """
    Iterate through all elements in the given GStreamer pipeline and set the qos property to False
    where applicable.
    When the 'qos' property is set to True, the element will measure the time it takes to process each
    buffer and will drop frames if latency is too high.
    We are running on long pipelines, so we want to disable this feature to avoid dropping frames.
    
    This function is taken almost completely from HAILO examples repo.
    """
    # Iterate through all elements in the pipeline
    it = pipeline.iterate_elements()
    while True:
        result, element = it.next()
        if result != Gst.IteratorResult.OK:
            break

        # Check if the element has the 'qos' property
        if 'qos' in GObject.list_properties(element):
            # Set the 'qos' property to False
            element.set_property('qos', False)
            log.debug(f"Set qos to False for {element.get_name()}")

def remote_uri_valid(uri: str) -> bool:
    """
    Return whether the given URI is a valid remote URI.
    """
    if uri.startswith("http") or uri.startswith("rtsp"):
        uri_parse = urllib.parse.urlparse(uri)
        ip_or_url, port = uri_parse.netloc.split(':')
        try:
            _ = int(port)
        except ValueError:
            return False
        return ip_or_url != ""
    else:
        return False

def source_uri_valid(source_uri: str) -> bool:
    """
    Return whether the given source URI is valid.
    """
    if os.path.isfile(source_uri):
        return True
    elif "pcie" in source_uri:
        return True
    elif remote_uri_valid(source_uri):
        return True
    else:
        return False

def sink_uri_valid(sink_uri: str) -> bool:
    """
    Return whether the given sink URI is valid.
    """
    if sink_uri == "display":
        return True
    elif remote_uri_valid(sink_uri):
        return True
    else:
        try:
            f = open(sink_uri, 'wb')
            f.close()
            os.remove(sink_uri)
        except Exception:
            return False
        return True
