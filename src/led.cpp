#include "esp32-hal-gpio.h"
#include <Arduino.h>
#include <atomic>
#include <esp_task.h>
#include <sdkconfig.h>

#ifndef NO_LED_FLASHING
#define NO_LED_FLASHING 0
#endif

// CONFIG_IDF_TARGET_ESP32C3 is defined by ESP-IDF for any C3-based board
// (including nologo_esp32c3_super_mini, not just the official Dev Module).
#ifndef CONFIG_IDF_TARGET_ESP32C3

#define LED_PIN 2

// 12.5% brightness
inline void LED_on() { ledcWrite(LED_PIN, 32); }
inline void LED_off() { ledcWrite(LED_PIN, 0); }
#else

#define LED_PIN 8

inline void LED_on() {
#ifdef NOLOGO_C3_SUPER_MINI
    digitalWrite(LED_PIN, LOW);
#else
    digitalWrite(LED_PIN, HIGH);
#endif
}
inline void LED_off() {
#ifdef NOLOGO_C3_SUPER_MINI
    digitalWrite(LED_PIN, HIGH);
#else
    digitalWrite(LED_PIN, LOW);
#endif
}

#endif

std::atomic<bool> Flashing(false);

struct Arguments {
    unsigned times;
    unsigned interval;
} FlashLight;

void flash_led(void *) {
    bool led_on = false;
    for (;;) {
        if (!Flashing.load()) {
            delay(50);
            continue;
        }
        if (FlashLight.times <= 0) {
            Flashing.store(false);
            LED_off();
            led_on = false;
            continue;
        }
        FlashLight.times--;
        led_on = !led_on;
        led_on ? LED_on() : LED_off();
        delay(FlashLight.interval);
    }
}

void start_flash_light(unsigned interval_ms, unsigned times) {
#if NO_LED_FLASHING
    return;
#endif
    // ignore if already flashing
    if (Flashing.load()) {
        return;
    }

    FlashLight.interval = interval_ms;
    FlashLight.times = times;
    Flashing.store(true);
}

void spawn_flash_task() {
#ifndef CONFIG_IDF_TARGET_ESP32C3
    const unsigned LED_FREQ = 5000;
    const unsigned char LED_RESOLUTION = 8;
    ledcAttach(LED_PIN, LED_FREQ, LED_RESOLUTION);
#else
    pinMode(LED_PIN, OUTPUT);
#endif

    LED_off();

    xTaskCreate(flash_led, "flash_led", 2000, NULL, ESP_TASK_PRIO_MAX - 1,
                NULL);
}
