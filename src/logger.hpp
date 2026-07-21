#pragma once
#include <cstdint>

void initialize_logger();

// 4 times per a minute
const constexpr uint32_t RECORD_INTERVAL{15'000};
