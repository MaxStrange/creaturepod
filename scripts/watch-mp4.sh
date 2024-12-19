# Usage: ./watch-mp4.sh path/to/video.mp4
gst-launch-1.0 filesrc location=$1 ! decodebin ! videoconvert ! autovideosink
