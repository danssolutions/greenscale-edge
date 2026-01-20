# sensors/turbidity_sensor.py
"""
Turbidity sensor (DFRobot SEN0189) on ADS1115 A0.

DFRobot calibration curve:

If voltage <= 2.5:
    NTU = 3000
Else:
    NTU = -1120.4 * V^2 + 5742.3 * V - 4352.9
"""

from datetime import datetime, UTC
from .adc import read_channel_mv

TURBIDITY_CHANNEL = 0  # ADS1115 A0

# based on sample code from https://wiki.dfrobot.com/Turbidity_sensor_SKU__SEN0189
# the original code assumes 5v, but we have 3.3v, so we bump up the scaling it


def voltage_to_ntu(volts: float) -> float:
    volts = volts * (5.0 / 3.3)
    if volts <= 2.5:
        return 3000.0
    return -1120.4 * volts * volts + 5742.3 * volts - 4352.9


def read():
    """Returns NTU."""
    mv = read_channel_mv(TURBIDITY_CHANNEL)
    volts = mv / 1000.0
    ntu = voltage_to_ntu(volts)

    return {
        "sensor": "turbidity",
        "value": round(ntu, 2),
        "units": "NTU",
        "status": "ok",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
