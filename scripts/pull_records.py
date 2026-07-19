#!/usr/bin/env python3
"""
One-shot script to fetch sensor records from ESP32 devices and push
them to an InfluxDB Line Protocol backend.

Usage:
    python pull_records.py [config_path]

    If config_path is omitted, defaults to 'config.toml' in the same
    directory as this script.

Config file format (TOML):
    See config.example.toml for a documented example.
"""

import logging
import os
import struct
import sys
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# HTTP port on the ESP32 devices
DEVICE_PORT = 8888

# Record binary format: uint64 timestamp + float temperature + float humidity
# All fields are little-endian, packed with no padding.
_RECORD_STRUCT = struct.Struct("<Qff")
RECORD_SIZE = _RECORD_STRUCT.size  # 16 bytes

# Request timeout in seconds
REQUEST_TIMEOUT = 10

# InfluxDB Line Protocol measurement name
MEASUREMENT = "environment"


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class Record:
    """A single sensor reading from an ESP32 device.

    Attributes:
        ts: Unix timestamp (seconds since epoch) when the reading was taken.
        temperature: Ambient temperature in degrees Celsius.
        humidity: Relative humidity in percent (0-100).
        host: IP address or hostname of the source device.
        name: Human-friendly location label for the device.
    """

    ts: int
    temperature: float
    humidity: float
    host: str
    name: str


class NodeConfig:
    """Configuration for a single ESP32 device."""

    __slots__ = ("host", "name")

    def __init__(self, host: str, name: str) -> None:
        self.host = host
        self.name = name


class AppConfig:
    """Top-level application configuration loaded from TOML."""

    __slots__ = ("post_url", "access_token", "nodes")

    def __init__(
        self, post_url: str, access_token: str, nodes: list[NodeConfig]
    ) -> None:
        self.post_url = post_url
        self.access_token = access_token
        self.nodes = nodes


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def load_config(path: str) -> AppConfig:
    """Parse a TOML config file and return an AppConfig instance.

    Args:
        path: Filesystem path to the TOML config file.

    Returns:
        An AppConfig populated from the file.

    Raises:
        FileNotFoundError: If the config file does not exist.
        tomllib.TOMLDecodeError: If the file is not valid TOML.
        KeyError: If a required field is missing.
        TypeError: If a field has the wrong type.
    """
    with open(path, "rb") as fh:
        data = tomllib.load(fh)

    post_url: str = data["post_url"]
    access_token: str = data.get("access_token", "")

    raw_nodes: list[dict] = data["node"]
    nodes: list[NodeConfig] = []
    for item in raw_nodes:
        nodes.append(NodeConfig(host=str(item["host"]), name=str(item["name"])))

    return AppConfig(post_url=post_url, access_token=access_token, nodes=nodes)


# ---------------------------------------------------------------------------
# Device communication
# ---------------------------------------------------------------------------


def fetch_records(host: str) -> bytes | None:
    """Fetch raw binary records from an ESP32 device.

    Performs a GET request to ``http://{host}:8888/records``.

    Args:
        host: IP address or hostname of the device.

    Returns:
        Raw response body bytes, or None on failure.
    """
    url = f"http://{host}:{DEVICE_PORT}/records"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return resp.read()
    except urllib.error.URLError as exc:
        log.error("  FAIL  fetch: %s", exc.reason)
        return None
    except TimeoutError:
        log.error("  FAIL  fetch: timed out after %ss", REQUEST_TIMEOUT)
        return None


def parse_records(data: bytes, host: str, name: str) -> list[Record]:
    """Decode a raw binary blob into a list of Records.

    The blob is a concatenation of 16-byte entries each encoded as
    little-endian uint64 (timestamp) + float32 (temperature) + float32
    (humidity).

    Args:
        data: Raw binary response body from the device.
        host: Device IP (attached to each Record for provenance).
        name: Human-friendly location name.

    Returns:
        List of decoded Record objects. May be empty.
    """
    count = len(data) // RECORD_SIZE
    records: list[Record] = []
    for idx in range(count):
        offset = idx * RECORD_SIZE
        chunk = data[offset : offset + RECORD_SIZE]
        ts, temperature, humidity = _RECORD_STRUCT.unpack(chunk)
        records.append(
            Record(
                ts=ts,
                temperature=temperature,
                humidity=humidity,
                host=host,
                name=name,
            )
        )
    return records


def trim_records(host: str) -> bool:
    """Instruct the device to delete all stored records.

    Performs a GET request to ``http://{host}:8888/trim_records``.

    Args:
        host: IP address or hostname of the device.

    Returns:
        True if the device responded with HTTP 200, False otherwise.
    """
    url = f"http://{host}:{DEVICE_PORT}/trim_records"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


# ---------------------------------------------------------------------------
# InfluxDB Line Protocol
# ---------------------------------------------------------------------------


def build_line_protocol(records: list[Record]) -> str:
    """Build an InfluxDB Line Protocol payload from a list of Records.

    One line per record, using the measurement name ``environment``
    with tags ``node`` and ``host``, fields ``temperature`` and
    ``humidity``, and a nanosecond-precision timestamp.

    Example line::

        environment,node=living_room \\
            temperature=23.5,humidity=60.2 1712345678000000000

    Args:
        records: Parsed sensor records.

    Returns:
        A newline-separated string suitable as the body of a write
        request to an InfluxDB-compatible endpoint.
    """
    lines: list[str] = []
    for rec in records:
        # Tags
        tag_node = _escape_tag(rec.name)
        # Fields
        temp_str = f"{rec.temperature:.1f}"
        hum_str = f"{rec.humidity:.1f}"
        # Timestamp in milliseconds
        ts_ns = rec.ts * 1_000

        lines.append(
            f"{MEASUREMENT},node={tag_node} "
            f"temperature={temp_str},humidity={hum_str} "
            f"{ts_ns}"
        )
    return "\n".join(lines)


def _escape_tag(value: str) -> str:
    """Escape a tag value per the Line Protocol spec.

    Commas, spaces, and equals signs must be backslash-escaped in tag
    values.
    """
    return (
        value.replace("\\", "\\\\")
        .replace(",", "\\,")
        .replace(" ", "\\ ")
        .replace("=", "\\=")
    )


def push_to_influxdb(post_url: str, access_token: str, payload: str) -> bool:
    """POST a Line Protocol payload to an InfluxDB-compatible endpoint.

    Args:
        post_url: Full URL of the InfluxDB write endpoint.
        access_token: Bearer token, or empty string for no auth.
        payload: Newline-separated Line Protocol data.

    Returns:
        True on HTTP 2xx, False otherwise.
    """
    body = payload.encode("utf-8")
    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Content-Length": str(len(body)),
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    req = urllib.request.Request(post_url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            if 200 <= resp.status < 300:
                return True
            log.error("  FAIL  push: HTTP %s", resp.status)
            return False
    except urllib.error.HTTPError as exc:
        log.error("  FAIL  push: HTTP %s %s", exc.code, exc.reason)
        return False
    except urllib.error.URLError as exc:
        log.error("  FAIL  push: %s", exc.reason)
        return False
    except TimeoutError:
        log.error("  FAIL  push: timed out after %ss", REQUEST_TIMEOUT)
        return False


# ---------------------------------------------------------------------------
# Logging helper
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _usage() -> str:
    return (
        "Usage: python pull_records.py [config_path]\n"
        "\n"
        "Fetch sensor records from ESP32 devices configured in a TOML file\n"
        "and push them to an InfluxDB Line Protocol backend.\n"
        "\n"
        "Arguments:\n"
        "  config_path   Path to TOML config file.\n"
        "                Defaults to 'config.toml' in the script's directory.\n"
        "\n"
        "Exit codes:\n"
        "  0   All nodes processed successfully.\n"
        "  1   One or more nodes failed."
    )


def main() -> int:
    """Entry point. Returns a process exit code."""

    # ---- CLI ----
    if "--help" in sys.argv or "-h" in sys.argv:
        print(_usage())
        return 0

    # Resolve config path
    if len(sys.argv) >= 2:
        config_path = sys.argv[1]
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config.toml")

    # ---- Load config ----
    try:
        cfg = load_config(config_path)
    except FileNotFoundError:
        log.error("Config file not found: %s", config_path)
        return 1
    except (tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        log.error("Config error in %s: %s", config_path, exc)
        return 1

    if not cfg.nodes:
        log.warning("No nodes defined in config; nothing to do.")
        return 0

    log.info("Loaded %s node(s) from %s", len(cfg.nodes), config_path)
    log.info("Post URL: %s", cfg.post_url)
    log.info("")

    # ---- Process each node ----
    all_ok = True

    for node in cfg.nodes:
        label = f"node={node.name}  host={node.host}"
        log.info("--- %s ---", label)

        # 1. Fetch
        raw = fetch_records(node.host)
        if raw is None:
            all_ok = False
            log.info("")
            continue
        fetch_ok = True

        # 2. Parse
        records = parse_records(raw, node.host, node.name)
        count = len(records)
        log.info("  fetched %s record(s) (%s bytes)", count, len(raw))

        # 3. Push
        if count == 0:
            log.info("  no records to push")
            push_ok = True
        else:
            payload = build_line_protocol(records)
            push_ok = push_to_influxdb(cfg.post_url, cfg.access_token, payload)
            if push_ok:
                log.info("  pushed %s record(s) OK", count)
            else:
                all_ok = False

        # 4. Trim (only if both fetch and push succeeded)
        if fetch_ok and push_ok and count:
            if trim_records(node.host):
                log.info("  trimmed OK")
            else:
                log.warning("  trim request failed (ignored)")
        else:
            log.warning("  SKIP  trim")

        log.info("")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
