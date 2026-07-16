#include <LittleFS.h>
#include <time.h>

#include "dht.hpp"
#include "logger.hpp"
#include "ssd1306.hpp"
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

    LittleFS.begin(true, "/storage", 1, "storage");

    spawn_wifi_task();
    initialize_dht();

    initialize_oled();
    connect_wifi();
    initialize_logger();

    configTime(3600 * 8,                       // UTC+8:00
               0,                              // DST offset
               "203.107.6.88", "47.96.149.233" // Alibaba NTP
    );
}

void loop(void) {
    display.clearDisplay();
    display.setCursor(0, 0);

    int rssi = WiFi.RSSI();
    if (!rssi && WIFI_DISCONNECTED) {
        Serial.println("Start reconnecting...");
        connect_wifi();
        Serial.println("Reconnected");
        return;
    }

    char timebuf[22];
    const char *const localtime = get_localtime(timebuf, sizeof(timebuf));

    display.setTextSize(1);
    display.println("");
    display.print(' ');
    display.println(localtime);
    display.println("");

    display.setTextSize(2);
    float temp = getTemperature();
    float humi = getHumidity();

    if (isnanf(temp)) {
        display.printf("  NaN");
    } else {
        display.printf("  %2.1f", temp);
    }

    display.setTextSize(1);
    display.printf(" o");
    display.setTextSize(2);
    display.printf("C\n");

    display.printf("  %2.1f %%\n", humi);

    display.display();

    delay(100);
}
