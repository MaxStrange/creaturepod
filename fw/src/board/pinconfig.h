/*
 * Pin configuration
 */
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <pico/stdlib.h>

// Note that pin numbers are the GPIO number. NOT the board pin number! //

/** LED: on-board */
static const uint PIN_LED = 25; // on board LED

/** GPS: RX to GPS; our TX */
static const uint PIN_GPS_TX = 0; // UART0 RX

/** GPS: TX from GPS; our RX */
static const uint PIN_GPS_RX = 1; // UART0 RX

// Optional PPS from GPS
// TODO (any old GPIO will do, I think)

/** NeoPixels */
static const uint PIN_LED_STRIPS_PIO = 3; // Pio

/** Flashlight */
// TODO: Any old GPIO

/** Temperature and humidity sensor: Data */
static const uint PIN_TEMP_AND_HUMIDITY_SDA = 2; // I2C1 SDA - One Wire protocol

/** SPI: connection to RPi: RX */
static const uint PIN_RPI_SPI_RX = 8; // SPI1 RX

/** SPI: connection to RPi: CS */
static const uint PIN_RPI_SPI_CS = 9; // SPI1 CSn

/** SPI: connection to RPi: SCK */
static const uint PIN_RPI_SPI_SCK = 10; // SPI1 SCK

/** SPI: connection to RPi: TX */
static const uint PIN_RPI_SPI_TX = 11; // SPI1 TX

/** I2C: Camera Multiplexer */
// TODO

/** IMU (if present) */

/** Interrupt connection from RPi? */
// TODO: I assume we will interrupt on the CS line, but need to confirm

/** RTC? */
// TODO: The RPi5 has an on-board RTC which can be powered with its own battery. Look into this

/** TPM? */

// Pin mappings
//Pin 0  GPS
//Pin 1  GPS
//Pin 2  Temperature/Humidity Sensor
//Pin 3  Neo Pixel Pio
//Pin 4
//Pin 5
//Pin 6
//Pin 7
//Pin 8  RPi SPI
//Pin 9  RPi SPI
//Pin 10 RPi SPI
//Pin 11 RPi SPI
//Pin 12
//Pin 13
//Pin 14
//Pin 15
//Pin 16
//Pin 17
//Pin 18
//Pin 19
//Pin 20
//Pin 21
//Pin 22
//Pin 23
//Pin 24
//Pin 25 On-board LED
//Pin 26
//Pin 27
//Pin 28

#ifdef __cplusplus
}
#endif
