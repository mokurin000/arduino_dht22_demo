#pragma once

#include <stdint.h>

struct record {
    uint64_t ts;
    float temperature;
    float humidity;
} __attribute__((packed));

static constexpr const char *RECORDS_FILE = "/dht22";
