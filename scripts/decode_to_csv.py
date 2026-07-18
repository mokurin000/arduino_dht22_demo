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

RECORD_STRUCT = struct.Struct("<Qff")  # uint64 LE, float32 LE, float32 LE


def main():
    if len(sys.argv) < 2:
        print("Usage: python decode_to_csv.py <ip> [name]", file=sys.stderr)
        print("  <ip>    IP address of the ESP32 (required)", file=sys.stderr)
        print("  [name]  Optional label for the CSV file", file=sys.stderr)
        sys.exit(1)

    ip = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else ""

    records_url = f"http://{ip}:8888/records"
    trim_url = f"http://{ip}:8888/trim_records"
    csv_file = f"export/records_{name}.csv" if name else "export/records.csv"

    # 下载记录
    with urllib.request.urlopen(records_url) as resp:
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

    write_header = not os.path.exists(csv_file)

    count = 0

    # 追加写入 CSV
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
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

    print(f"Appended {count} records to {csv_file}", file=sys.stderr)

    # 写入成功后通知 ESP32 删除已获取记录
    with urllib.request.urlopen(trim_url):
        pass

    print("Trim completed.", file=sys.stderr)


if __name__ == "__main__":
    main()
