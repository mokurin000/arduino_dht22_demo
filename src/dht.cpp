#include "dht.hpp"

static DHT dht(DHT22_DAT_PIN, DHT22);

static std::atomic<float> Temperature{NAN}, Humidity{NAN};

void dht_loop(void *) {
    delay(2000); // warm up DHT22

    for (;;) {
        unsigned long start = millis();

        float temperature = dht.readTemperature();
        float humidity = dht.readHumidity();

        Temperature.store(temperature, std::memory_order::release);
        Humidity.store(humidity, std::memory_order::release);

        unsigned long elapsed = millis() - start;
        delay((elapsed < 2000) ? (2000 - elapsed) : 0);
    }
}

void initialize_dht() {
    dht.begin();

    xTaskCreate(dht_loop, "dht_read_data", 4000, NULL, ESP_TASK_PRIO_MAX - 1,
                NULL);
}

float getTemperature() { return Temperature.load(std::memory_order::acquire); }
float getHumidity() { return Humidity.load(std::memory_order::acquire); }
