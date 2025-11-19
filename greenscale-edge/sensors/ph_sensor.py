# sensors/ph_sensor.py
"""
pH sensor (DFRobot SEN0169-V2) on ADS1115 A1.

Calibration points (3.3V supply):
    pH 10 -> 1.05 V
    pH  7 -> 1.50 V
    pH  4 -> 2.00 V

Least-squares fit gives:
    pH = PH_M * V + PH_B
"""

from datetime import datetime, UTC
from .adc import read_channel_mv

PH_CHANNEL = 1  # ADS1115 A1

# Calibration coefficients (from your buffer data)
PH_M = -6.31
PH_B = 16.57


def voltage_to_ph(volts: float) -> float:
    ph = PH_M * volts + PH_B
    # Clamp to a sensible range
    return max(0.0, min(14.0, ph))


def read():
    """
    Read pH via ADS1115 and return calibrated pH value.
    """
    mv = read_channel_mv(PH_CHANNEL)
    volts = mv / 1000.0
    ph_value = voltage_to_ph(volts)

    return {
        "sensor": "ph",
        "value": round(ph_value, 2),
        "units": "pH",
        "status": "ok",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
