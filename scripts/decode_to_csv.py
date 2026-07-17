#!/usr/bin/env python3
"""
Download DHT22 records from ESP32 and append to records.csv.

Record layout (little-endian):
    uint64_t timestamp
    float    temperature
    float    humidity
"""

import csv
import os
import struct
import sys
import urllib.request
from datetime import datetime

RECORDS_URL = "http://192.168.1.103:8888/records"
TRIM_URL = "http://192.168.1.103:8888/trim_records"

CSV_FILE = "records.csv"

RECORD_STRUCT = struct.Struct("<Qff")  # uint64 LE, float32 LE, float32 LE


def main():
    # 下载记录
    with urllib.request.urlopen(RECORDS_URL) as resp:
        data = resp.read()

    if len(data) == 0:
        print("No records.", file=sys.stderr)
        return

    if len(data) % RECORD_STRUCT.size != 0:
        print(
            f"Error: file size ({len(data)}) is not a multiple of "
            f"{RECORD_STRUCT.size} bytes.",
            file=sys.stderr,
        )
        sys.exit(1)

    write_header = not os.path.exists(CSV_FILE)

    count = 0

    # 追加写入 CSV
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if write_header:
            writer.writerow(["localtime", "temperature", "humidity"])

        for offset in range(0, len(data), RECORD_STRUCT.size):
            ts, temperature, humidity = RECORD_STRUCT.unpack_from(data, offset)

            localtime = (
                datetime.fromtimestamp(ts).astimezone().isoformat(timespec="seconds")
            )

            writer.writerow(
                [
                    localtime,
                    f"{temperature:.1f}",
                    f"{humidity:.1f}",
                ]
            )

            count += 1

    print(f"Appended {count} records to {CSV_FILE}", file=sys.stderr)

    # 写入成功后通知 ESP32 删除已获取记录
    with urllib.request.urlopen(TRIM_URL):
        pass

    print("Trim completed.", file=sys.stderr)


if __name__ == "__main__":
    main()
