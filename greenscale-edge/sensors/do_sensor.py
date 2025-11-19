# sensors/do_sensor.py
"""
Dissolved Oxygen sensor (DFRobot SEN0237) on ADS1115 A2.

Very simple linear calibration based on lab notes:

    0% oxygen   -> 0.04 V  -> 0 mg/L
    saturated ~20°C -> 1.29 V -> ~9.1 mg/L (air-saturated water)

So:
    DO (mg/L) ~= DO_SLOPE * (V - DO_V_OFFSET)

This ignores temperature compensation and assumes the production
setup uses the same supply and amplifier gain as during calibration.
"""

from datetime import datetime, UTC
from .adc import read_channel_mv

DO_CHANNEL = 2  # ADS1115 A2

DO_V_OFFSET = 0.04      # volts at 0 mg/L (0% oxygen)
DO_SLOPE = 7.28         # mg/L per volt over DO_V_OFFSET


def voltage_to_do_mg_l(volts: float) -> float:
    do = DO_SLOPE * max(0.0, volts - DO_V_OFFSET)
    # A basic sanity clamp; adjust if your system can exceed this.
    return max(0.0, min(20.0, do))


def read():
    """
    Read DO sensor and return approximate dissolved oxygen in mg/L.
    """
    mv = read_channel_mv(DO_CHANNEL)
    volts = mv / 1000.0
    do_value = voltage_to_do_mg_l(volts)

    return {
        "sensor": "dissolved_oxygen",
        "value": round(do_value, 2),
        "units": "mg/L",
        "status": "ok",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
