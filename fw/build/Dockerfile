#
# Build from 'fw' folder directly.
#
FROM ubuntu:24.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    gcc-arm-none-eabi \
    libnewlib-arm-none-eabi \
    build-essential \
    git \
    libstdc++-arm-none-eabi-newlib \
    python3 \
    wget \
    && \
    apt-get autoclean -y && apt-get autoremove -y

# Create /pico/src directory
WORKDIR /pico
RUN mkdir -p /pico/src/

# Clone the repos
ARG PICO_RELEASE=1.5.1
RUN git clone --depth 1 --branch ${PICO_RELEASE} --recurse-submodules https://github.com/raspberrypi/pico-sdk.git
RUN git clone --depth 1 --branch sdk-${PICO_RELEASE} https://github.com/raspberrypi/pico-examples.git
RUN git clone --depth 1 --branch sdk-${PICO_RELEASE} https://github.com/raspberrypi/pico-extras.git
RUN git clone --depth 1 --branch sdk-${PICO_RELEASE} https://github.com/raspberrypi/pico-playground.git
RUN cp /pico/pico-sdk/external/pico_sdk_import.cmake /pico/src/pico_sdk_import.cmake
ENV PICO_SDK_PATH=/pico/pico-sdk

# Copy the source code into the container
COPY ./src /pico/src
WORKDIR /pico/src/build

# Build
ARG BUILD_TYPE=Debug
RUN cmake -DCMAKE_BUILD_TYPE=${BUILD_TYPE} .. && make -j4

CMD [ "/bin/bash", "-c", "echo 'build artifacts are located in /pico/src/build/' && sleep infinity" ]
