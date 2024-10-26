#! /bin/bash
# Run this on the Raspberry Pi if not using a Yocto image.
# Run from this directory

# Install apt dependencies
sudo apt-get update
sudo apt-get install -y python3 vim git python3-smbus2 python3-picamera2 openocd

# Install application and dependencies
cd ../app
pip install -e .[rpi]

# Install things necessary for Waveshare display
dtoverlay=vc4-kms-v3d
#DSI1 Use
dtoverlay=vc4-kms-dsi-waveshare-panel,4_0_inch
#DSI0 Use
#dtoverlay=vc4-kms-dsi-waveshare-panel,4_0_inch,dsi0

# Install the brightness script
wget https://files.waveshare.com/upload/f/f4/Brightness.zip
unzip Brightness.zip
cd Brightness
sudo chmod +x install.sh
./install.sh

# Install 
