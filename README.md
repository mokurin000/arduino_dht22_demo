# dht22 monitor

DHT22 Temperature & Relative Humidity monitor.

This project features a [web dashboard](https://mokurin000.github.io/arduino_dht22_demo).

## Hardware requirement

> [!WARNING]
>
> The `src/partitions.csv` is hard-coded for 4MB Flash, if you have larger SPI Flash,
> you need to modify it to take advantage.
>
> By default, the device is capable to store data standalone for about four months.
> Also, it refuses to persist records until RTC has time after `2026-01-01`.

- ESP32 or ESP32C3 board, 4MiB flash or more.
- DHT22

1. Connect `DHT22:DAT` with GPIO 3 for `esp32c3`, GPIO 17 for `esp32`.
2. Power up `DHT22:VCC` with `esp:VCC`.
3. Connect `DHT22:GND` with `esp:GND`.

## Development

In VSCode, setup `pioarduino`, and reload window, wait for automatic installation.

> [!NOTE]
>
> You may need to select your pioaruduino Intelli Sense Engine,
>
> by default it generates configuration for Microsoft C/C++.

Once setup pioarduino, you could type `Command+Alt+P` and perform `pioarduino: Build` or `pioarduino: Upload`.
