#include <time.h>

#include "dht.hpp"
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

    spawn_wifi_task();
    initialize_dht();

    initialize_oled();
    connect_wifi();

    configTime(3600 * 8,                       // UTC+8:00
               0,                              // DST offset
               "203.107.6.88", "47.96.149.233" // Alibaba NTP
    );
}

void loop(void) {
    display.clearDisplay();
    display.setCursor(0, 0);

    display.setTextSize(1);

    int rssi = WiFi.RSSI();
    if (!rssi && WIFI_DISCONNECTED) {
        Serial.println("Start reconnecting...");
        connect_wifi();
        Serial.println("Reconnected");
        return;
    }

    char timebuf[22];
    const char *const localtime = get_localtime(timebuf, sizeof(timebuf));
    display.print(' ');
    display.println(localtime);

    display.setTextSize(2);
    float temp = getTemperature();
    float humi = getHumidity();

    if (isnanf(temp)) {
        display.printf("NaN C\n");
    } else {
        display.printf("%.1f C\n", temp);
    }

    display.display();

    delay(100);
}
