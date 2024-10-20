cmake_minimum_required(VERSION 3.13)
include(pico_sdk_import.cmake)
project(podfw C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

# Add compiler definitions
#add_compile_definitions(LOG_LEVEL=${LOG_LEVEL})  # An example of how to do this

# Compiler warnings
add_compile_options(-Wall -Wextra -Werror -Wno-unused-function -Wno-unused-parameter)

# Add local source files
file(GLOB SOURCES
  "*.c"
  "board/*.c"
)

# Add local includes
include_directories(
  "."
  "board"
)

# Add the top-level executable
add_executable(podfw ${SOURCES})

# Link all the libraries
target_link_libraries(podfw
  pico_stdlib
  pico_multicore
  hardware_spi
  hardware_i2c
  hardware_pwm
  hardware_gpio
  hardware_clocks
  pico_time
)

# Some helpful pico* things
pico_add_extra_outputs(podfw)
pico_enable_stdio_usb(podfw 1)
