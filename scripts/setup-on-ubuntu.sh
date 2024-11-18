#! /bin/bash
# Run from this directory

# Make sure to install python3.12
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update
sudo apt-get install -y python3.12-full \
                        python3.12-dev \
                        python3.12-distutils

sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

# Check Python version
python --version | grep 3.12

python -m ensurepip --upgrade
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools

# Install apt dependencies
sudo apt-get update
sudo apt-get install -y \
                        vim \
                        git \
                        build-essential \
                        graphviz \
                        ffmpeg \
                        x11-utils \
                        libgraphviz-dev \
                        libgirepository1.0-dev \
                        libzmq3-dev \
                        openocd \
                        cmake \
                        libcairo2-dev \
                        libgstreamer1.0-dev \
                        libgstreamer-plugins-base1.0-dev \
                        libgstreamer-plugins-bad1.0-dev \
                        gstreamer1.0-plugins-base \
                        gstreamer1.0-plugins-good \
                        gstreamer1.0-plugins-bad \
                        gstreamer1.0-plugins-ugly \
                        gstreamer1.0-libav \
                        gstreamer1.0-tools \
                        gstreamer1.0-x \
                        gstreamer1.0-alsa \
                        gstreamer1.0-gl \
                        gstreamer1.0-gtk3 \
                        gstreamer1.0-qt5 \
                        gstreamer1.0-pulseaudio
#                        python3-gst-1.0
#                        python3-smbus2

# Install python3.12 version of gi
python -m pip install --ignore-installed PyGObject

# Install application and dependencies
cd ../app
python -m pip install -e .
