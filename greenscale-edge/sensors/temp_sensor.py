# sensors/temp_sensor.py
import glob
import os
import time
from datetime import datetime, UTC

BASE_DIR = "/sys/bus/w1/devices"
DEVICE_GLOB = BASE_DIR + "/28*"

# Load kernel modules once (they're usually auto-loaded after boot, but harmless)
os.system("modprobe w1-gpio")
os.system("modprobe w1-therm")


def _get_device_file() -> str:
    """Locate the first DS18B20 sensor device file."""
    devices = glob.glob(DEVICE_GLOB)
    if not devices:
        raise RuntimeError(
            "No DS18B20 temperature sensors found under /sys/bus/w1/devices")
    return os.path.join(devices[0], "w1_slave")


DEVICE_FILE = _get_device_file()


def _read_raw_lines():
    with open(DEVICE_FILE, "r") as f:
        return f.readlines()


def read_temp_c() -> float:
    """
    Read temperature in °C from DS18B20.
    Retries until the CRC line ends in 'YES'.
    """
    lines = _read_raw_lines()
    # Wait until CRC is OK
    retries = 5
    while lines[0].strip()[-3:] != "YES" and retries > 0:
        time.sleep(0.2)
        lines = _read_raw_lines()
        retries -= 1

    # Second line contains 't=xxxxx'
    equals_pos = lines[1].find("t=")
    if equals_pos == -1:
        raise RuntimeError("Unexpected DS18B20 data format")

    temp_string = lines[1][equals_pos + 2:]
    temp_c = float(temp_string) / 1000.0
    return temp_c


def read():
    """
    Read temperature sensor and return temperature in Celsius.
    """
    temp_c = read_temp_c()
    return {
        "sensor": "temperature",
        "value": round(temp_c, 2),
        "units": "degC",
        "status": "ok",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
