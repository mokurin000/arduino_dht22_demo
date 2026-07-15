#!/usr/bin/env python3
"""
Download DHT22 records from ESP32 and output CSV.

Record layout (little-endian):
    uint64_t timestamp
    float    temperature
    float    humidity

Usage:
    python fetch_records.py > records.csv
"""

import csv
import struct
import sys
import urllib.request
from datetime import datetime

URL = "http://192.168.1.103:8888/records"

RECORD_STRUCT = struct.Struct("<Qff")  # uint64 LE, float32 LE, float32 LE


def main():
    with urllib.request.urlopen(URL) as resp:
        data = resp.read()

    if len(data) % RECORD_STRUCT.size != 0:
        print(
            f"Error: file size ({len(data)}) is not a multiple of "
            f"{RECORD_STRUCT.size} bytes.",
            file=sys.stderr,
        )
        exit(1)

    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["localtime", "temperature", "humidity"])

    for offset in range(0, len(data) - RECORD_STRUCT.size + 1, RECORD_STRUCT.size):
        ts, temperature, humidity = RECORD_STRUCT.unpack_from(data, offset)

        localtime = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

        writer.writerow(
            [
                localtime,
                f"{temperature:.1f}",
                f"{humidity:.1f}",
            ]
        )


if __name__ == "__main__":
    main()
