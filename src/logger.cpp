#include <LittleFS.h>
#include <WebServer.h>
#include <ctime>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <time.h>

#include "common.hpp"
#include "dht.hpp"
#include "logger.hpp"

static constexpr uint64_t MIN_VALID_TIMESTAMP =
    1767225600ULL; // 2026-01-01 00:00:00 GMT

static SemaphoreHandle_t storage_mutex = NULL;
static WebServer server(8888);

// ---- record writing ----

static void logger_task(void *) {
    for (;;) {
        unsigned long start = millis();

        float temperature = getTemperature();
        float humidity = getHumidity();

        if (isnanf(temperature) || isnanf(humidity)) {
            delay(2000); // wait for new value
            continue;
        }

        // NTP not working, skip it
        time_t now;
        time(&now);
        if (now < (time_t)MIN_VALID_TIMESTAMP) {
            delay(1000); // wait for NTP sync
            continue;
        }

        xSemaphoreTake(storage_mutex, portMAX_DELAY);

        File f = LittleFS.open(RECORDS_FILE, FILE_APPEND);
        if (f) {
            record r = {(uint64_t)now, temperature, humidity};
            f.write((uint8_t *)&r, sizeof(r));
            f.close();
        }

        xSemaphoreGive(storage_mutex);

        // wait until next append
        unsigned long elapsed = millis() - start;
        delay((elapsed < RECORD_INTERVAL) ? (RECORD_INTERVAL - elapsed) : 0);
    }
}

// ---- web server handlers ----

static void handle_root() {
    time_t timestamp;
    time(&timestamp);

    float temperature = getTemperature();
    float humidity = getHumidity();

    char buffer[128];
    sprintf(buffer,
            "{\"timestamp\":%llu,\"temperature\":%.1f,\"humidity\":%.1f}",
            timestamp, temperature, humidity);

    server.send(200, "application/json", buffer);
}

static void handle_records() {
    xSemaphoreTake(storage_mutex, portMAX_DELAY);

    File f = LittleFS.open(RECORDS_FILE, FILE_READ);
    if (f) {
        server.streamFile(f, "application/octet-stream");
        f.close();
    } else {
        server.send(404, "text/plain", "No records");
    }

    xSemaphoreGive(storage_mutex);
}

static void handle_trim_records() {
    xSemaphoreTake(storage_mutex, portMAX_DELAY);

    File f = LittleFS.open(RECORDS_FILE, FILE_WRITE);
    if (f) {
        f.close();
    }

    xSemaphoreGive(storage_mutex);

    server.send(200, "text/plain", "OK");
}

static void server_task(void *) {
    sleep(5); // waits for initialization

    server.on("/", handle_root);
    server.on("/records", handle_records);
    server.on("/trim_records", handle_trim_records);
    server.begin();

    for (;;) {
        server.handleClient();
        delay(10);
    }
}

// ---- public API ----

void initialize_logger() {
    storage_mutex = xSemaphoreCreateMutex();

    xTaskCreate(logger_task, "dht_logger", 4000, NULL, ESP_TASK_PRIO_MAX - 1,
                NULL);
    xTaskCreatePinnedToCore(server_task, "dht_server", 8192, nullptr,
                            ESP_TASK_PRIO_MIN + 1, nullptr,
                            ARDUINO_RUNNING_CORE);
}
