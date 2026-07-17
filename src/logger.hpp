#pragma once
#include <cstdint>

void initialize_logger();

// twice per a minute
const constexpr uint32_t RECORD_INTERVAL{30'000};
