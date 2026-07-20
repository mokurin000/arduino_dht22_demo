if [ -d "./.pio/build/wokwi" ]; then
    (
        cd .pio/build/wokwi
        esptool --chip esp32 \
            merge-bin \
            -o firmware.uf2 \
            --flash-mode qio \
            --format uf2 \
            0x1000 bootloader.bin \
            0x8000 partitions.bin \
            0x10000 firmware.bin
        mv firmware.uf2 ../../../wokwi/esp32/
    )
fi

# TODO: fix c3 mini emulation crash
if [ -d "./.pio/build/wokwi-c3-mini" ]; then
    (
        cd .pio/build/wokwi-c3-mini
        esptool --chip esp32c3 \
            merge-bin \
            -o firmware.uf2 \
            --flash-mode qio \
            --format uf2 \
            0x0 bootloader.bin \
            0x8000 partitions.bin \
            0x10000 firmware.bin
        mv firmware.uf2 ../../../wokwi/esp32-c3/
    )
fi
