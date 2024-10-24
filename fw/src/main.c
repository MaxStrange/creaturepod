// Stdlib includes
#include <stdbool.h>
#include <stdio.h>
// SDK includes
#include "pico/stdlib.h"
#include "hardware/spi.h"
// Library includes
// Local includes
#include "board/pinconfig.h"

/**
 * @brief Main entry point
 *
 * @return int
 */
int main(void)
{
    // Initialize the core system
    // TODO: is there anything to do here? Maybe multicore stuff?
    //       Clock configuration?
    //       Wakeup-interrupt enable?

    // Initialize UART for debugging (in a release build, this should be turned off from the CMake build system)
    stdio_init_all();

    // Initialize the on-board LED for debugging (in a release build, this should be turned off to save power)
    // TODO

    // Initialize the flashlight LED
    // TODO

    // Initialize the LED strip subsystem
    // TODO

    // Initialize the sensor subsystem
    // TODO

    // Initialize the SPI bus for comms with the motherboard
    // TODO

    while (true)
    {
        ; // Do nothing for now
    }
}
