#include <atomic>

#include "WiFiGeneric.h"
#include "led.hpp"
#include "wifi.hpp"

#ifdef USING_WOKWI
const char *ssid = "Wokwi-GUEST";
const char *password = "";
#else
const char *ssid = "Mk-wifi";
const char *password = "Ewm4HmMzOMU";
#endif

std::atomic<bool> ResetWifi(false);

// Tracks whether WiFi.begin() has ever been called.
// Used instead of WiFi.getMode() to guard WiFi.disconnect(),
// because getMode() returns stale values even when the WiFi
// driver hasn't finished initializing (esp. on ESP32-C3 where
// RF calibration is slow).
static std::atomic<bool> WifiEverStarted(false);

void reset_wifi(void *) {
    for (;;) {
        if (ResetWifi.load()) {
            // Only disconnect if WiFi.begin() has been called at least once.
            // On first boot, WiFi.getMode() may return WIFI_STA (from a
            // previous mode() call) but the driver isn't initialized yet,
            // causing ESP_ERR_WIFI_NOT_INIT.
            if (WifiEverStarted.load()) {
                WiFi.disconnect(true);
            }

            WiFi.mode(WIFI_MODE_STA);
            WiFi.begin(ssid, password);

#ifdef NOLOGO_C3_SUPER_MINI
            Serial.println("[WiFi] decreasing tx power for super mini");
            WiFi.setTxPower(WIFI_POWER_11dBm);
#endif

            WifiEverStarted.store(true);
            ResetWifi.store(false);
        } else {
            delay(500);
        }
    }
}

void spawn_wifi_task() {
    xTaskCreate(reset_wifi, "wifi_reset", 4000, nullptr, ESP_TASK_PRIO_MAX - 1,
                nullptr);
}

/*
must call after initialized OLED
*/
void connect_wifi() {
    const int MAX_RETRIES = 3; // outer loop retries (each = up to ~10 s)
    int retries = 0;

    while (WIFI_DISCONNECTED && retries < MAX_RETRIES) {
        retries++;
        Serial.printf("[WiFi] Connection attempt %d/%d...\n", retries,
                      MAX_RETRIES);

        ResetWifi.store(true);
        // Give the reset_wifi task time to process the flag before polling
        delay(100);

        int times = 0;
        while (++times < 20 && WIFI_DISCONNECTED) {
            start_flash_light(250, 1);
            delay(500);
        }

        if (WIFI_DISCONNECTED) {
            Serial.println("[WiFi] Timed out, waiting 2 s before retry...");
            delay(2000);
        }
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.print("[WiFi] Connected. IP: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("[WiFi] FAILED to connect after max retries.");
    }
}