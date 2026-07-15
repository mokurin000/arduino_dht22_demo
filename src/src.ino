#include <SPIFFS.h>
#include <time.h>

#include "dht.hpp"
#include "led.hpp"
#include "logger.hpp"
#include "wifi.hpp"

// SAFETY: this function is neither reentrant nor thread-safe.
const char *get_localtime(char *buf, size_t buf_len) {
    time_t rawtime;
    // get RTC timer
    time(&rawtime);

    // get local time
    const struct tm *const tzinfo = localtime(&rawtime);
    strftime(buf, buf_len, "%Y-%m-%d %H:%M:%S", tzinfo);
    return buf;
}

void setup(void) {
    Serial.begin(115200);
    Serial.println("Start initialization...");

    SPIFFS.begin(true);

    spawn_flash_task();

    spawn_wifi_task();
    initialize_dht();

    connect_wifi();
    initialize_logger();

    configTime(3600 * 8,                       // UTC+8:00
               0,                              // DST offset
               "203.107.6.88", "47.96.149.233" // Alibaba NTP
    );
}

void loop(void) { delay(100); }
