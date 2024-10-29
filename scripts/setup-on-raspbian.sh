#! /bin/bash
# Run this on the Raspberry Pi if not using a Yocto image.
# Run from this directory

# Install apt dependencies
sudo apt-get update
sudo apt-get install -y python3 vim git python3-smbus2 python3-picamera2 openocd hailo-all

# Install application and dependencies
cd ../app
pip install -e .[rpi]

# Install things necessary for Waveshare display
echo "\
dtoverlay=vc4-kms-v3d\n\
dtoverlay=vc4-kms-dsi-waveshare-panel,4_0_inch\n\
" | sudo tee -a /boot/firmware/config.txt > /dev/null

# Install the brightness script
cd ../
wget https://files.waveshare.com/upload/f/f4/Brightness.zip
unzip Brightness.zip
cd Brightness
sudo chmod +x install.sh
./install.sh
cd ../

# Install Camera
# TODO: Once the camera muxing is figured out

# Install Hailo
echo "dtparam=pciex1_gen=3" | sudo tee -a /boot/firmware/config.txt > /dev/null

# Reboot
echo "Done. Some changes require a reboot to take effect."
