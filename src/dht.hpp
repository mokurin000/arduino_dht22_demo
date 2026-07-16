#pragma once

#include <DHT.h>
#include <atomic>
#include <stdint.h>

void initialize_dht();

float getTemperature();
float getHumidity();

#ifdef ARDUINO_ESP32C3_DEV
const uint8_t DHT22_DAT_PIN = 3;
#else
const uint8_t DHT22_DAT_PIN = 17;
#endif
