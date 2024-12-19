gst-launch-1.0 -e libcamerasrc ! video/x-h264, width=800, height=448, framerate=30/1 ! avdec_h264 ! xvimagesink sync=false
