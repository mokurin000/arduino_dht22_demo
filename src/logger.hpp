#pragma once
#include <cstdint>

void initialize_logger();

// 12 times per a minute
const constexpr uint32_t RECORD_INTERVAL{5'000};
