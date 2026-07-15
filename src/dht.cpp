#include "dht.hpp"

static DHT dht = DHT(DHT22_DAT_PIN, DHT22);

static std::atomic<float> Temperature{NAN}, Humidity{NAN};

void dht_loop(void *) {
    for (;;) {
        // wait for two seconds before first reading
        delay(2000);

        float temperature = dht.readTemperature();
        float humidity = dht.readHumidity();

        Temperature.store(temperature, std::memory_order::release);
        Humidity.store(humidity, std::memory_order::release);
    }
}

void initialize_dht() {
    dht.begin();

    xTaskCreate(dht_loop, "dht_read_data", 4000, NULL, ESP_TASK_PRIO_MAX - 1,
                NULL);
}

float getTemperature() { return Temperature.load(std::memory_order::acquire); }
float getHumidity() { return Humidity.load(std::memory_order::acquire); }
