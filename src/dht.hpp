#pragma once

#include <DHT.h>
#include <atomic>
#include <stdint.h>

void initialize_dht();

float getTemperature();
float getHumidity();

const uint8_t DHT22_DAT_PIN = 17;
