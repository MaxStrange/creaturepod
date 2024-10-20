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
    // Initialize UART for debugging (in a release build, this should be turned off from the CMake build system)
    stdio_init_all();

    while (true)
    {
        ; // Do nothing for now
    }
}
