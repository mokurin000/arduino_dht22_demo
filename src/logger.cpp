#include <SPIFFS.h>
#include <time.h>

#include "dht.hpp"
#include "logger.hpp"

static constexpr uint64_t MIN_VALID_TIMESTAMP =
    1767225600ULL; // 2026-01-01 00:00:00 GMT

static void logger_task(void *) {
    for (;;) {
        delay(60000); // once per minute

        float temperature = getTemperature();
        float humidity = getHumidity();

        if (isnanf(temperature) || isnanf(humidity)) {
            continue;
        }

        // NTP not working, skip it
        time_t now = time(nullptr);
        if (now < (time_t)MIN_VALID_TIMESTAMP) {
            continue;
        }

        File f = SPIFFS.open("/dht22", FILE_APPEND);
        // File open failed, continue
        if (!f) {
            continue;
        }

        uint64_t ts = (uint64_t)now;
        f.write((uint8_t *)&ts, sizeof(ts));
        f.write((uint8_t *)&temperature, sizeof(temperature));
        f.write((uint8_t *)&humidity, sizeof(humidity));
        f.close();
    }
}

void initialize_logger() {
    xTaskCreate(logger_task, "dht_logger", 4000, NULL, ESP_TASK_PRIO_MAX - 1,
                NULL);
}
