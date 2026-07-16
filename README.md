# temperature screen

## Build with Arduino

Before start, you must have `Adafruit SSD1306` installed.

- Connect the `OLED:VCC` with a 5V or 3.3V power supplyment (according to the vendor)
- Connect `OLED:GND` with `ESP:GND` if you used `3.3V`/`VIN` on the board, or `*:GND` for an external power.
- Connect `ESP:D33` with `OLED:SDA`, and connect `ESP:D32` with `OLED:SDL`.

Now edit the Wifi SSID and password, compile and upload.

## Build with VSCode/pioarduino

To have a better expierence than Arduino IDE, setup `pioarduino`, and reload window, wait for automatic installation.

> [!NOTE]
>
> You should select your pioaruduino Intelli Sense Engine,
>
> by default it generates configuration for Microsoft C/C++.

Once setup pioarduino, you could type `Command+Alt+P` and select `pioarduino: Build`.
