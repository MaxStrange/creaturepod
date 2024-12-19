# Usage: ./record-mp4.sh <file-to-save.mp4>
gst-launch-1.0 -e libcamerasrc ! video/x-raw, format=RGB, width=640, height=640  ! videoconvert ! x264enc ! mp4mux ! filesink location=$1
