# Usage: ./watch-h264.sh path/to/video.h264
gst-launch-1.0 filesrc location=$1 ! h264parse ! avdec_h264 max-threads=2 ! videoconvert n-threads=2 ! autovideosink
