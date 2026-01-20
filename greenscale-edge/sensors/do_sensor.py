# sensors/do_sensor.py
"""
Dissolved Oxygen sensor (DFRobot SEN0237) on ADS1115 A2.

This follows the DFRobot Arduino example:
 - Temperature-dependent saturation table (0–40 °C)
 - Two-point calibration of saturation voltage

We read:
  - sensor voltage (mV) from ADS1115 (channel A2)
  - water temperature (°C) from temp_sensor.read_temp_c()
and compute DO in mg/L.
"""

from datetime import datetime, UTC

from .adc import read_channel_mv
from .temp_sensor import read_temp_c

DO_CHANNEL = 2  # ADS1115 A2

# ----------------- Two-point calibration ONLY -----------------
# CAL1: high-temperature calibration point
# CAL2: low-temperature calibration point
CAL1_T_C = 20.75      # °C at high-temp calibration
CAL1_V_MV = 750.0   # mV at CAL1_T_C in air-saturated water

CAL2_T_C = 30.44      # °C at low-temp calibration
CAL2_V_MV = 860.0   # mV at CAL2_T_C in air-saturated water


def _saturation_voltage_mv(voltage_mv: float, temp_c: float) -> float:
    """
    Two-point calibration line for saturation voltage V_sat(T):

        V_sat = (T - CAL2_T) * (CAL1_V - CAL2_V)/(CAL1_T - CAL2_T) + CAL2_V
    """
    # denom = (CAL1_T_C - CAL2_T_C)
    # if denom == 0:
    #     # Avoid div-by-zero if someone misconfigures the constants.
    #     return CAL1_V_MV
    # return ((temp_c - CAL2_T_C) * (CAL1_V_MV - CAL2_V_MV) / denom) + CAL2_V_MV
    V_sat = (temp_c - CAL2_T_C) * (CAL1_V_MV - CAL2_V_MV) / \
        (CAL1_T_C - CAL2_T_C) + CAL2_V_MV
    print(voltage_mv * DO_TABLE_UG_L[int(temp_c)] / V_sat)
    return (voltage_mv * DO_TABLE_UG_L[int(temp_c)] / V_sat)


# ----------------- DO saturation table (0–40 °C) -----------------
# Values in µg/L (mg/L * 1000), from DFRobot example code.
DO_TABLE_UG_L = [
    14460, 14220, 13820, 13440, 13090, 12740, 12420, 12110, 11810, 11530,
    11260, 11010, 10770, 10530, 10300, 10080, 9860,  9660,  9460,  9270,
    9080,  8900,  8730,  8570,  8410,  8250,  8110,  7960,  7820,  7690,
    7560,  7430,  7300,  7180,  7070,  6950,  6840,  6730,  6630,  6530,
    6410,
]

MIN_TABLE_TEMP_C = 0
MAX_TABLE_TEMP_C = 40


def _temperature_index(temp_c: float) -> int:
    """
    Clamp and round temperature to a valid index into DO_TABLE_UG_L.
    Table is defined for 0–40 °C.
    """
    idx = int(round(temp_c))
    if idx < MIN_TABLE_TEMP_C:
        idx = MIN_TABLE_TEMP_C
    if idx > MAX_TABLE_TEMP_C:
        idx = MAX_TABLE_TEMP_C
    return idx


def mv_and_temp_to_do_mg_l(voltage_mv: float, temp_c: float) -> float:
    """
    Core conversion: sensor voltage (mV) + temperature (°C) -> DO in mg/L.
    Mirrors the DFRobot Arduino logic.
    """
    idx = _temperature_index(temp_c)
    do_sat_ug_l = DO_TABLE_UG_L[idx]  # saturation DO at this T (µg/L)

    v_sat = _saturation_voltage_mv(voltage_mv, temp_c)
    if v_sat <= 0:
        # Bad calibration; avoid junk.
        return 0.0

    # Arduino formula:
    #   DO_raw(µg/L) = voltage_mv * DO_Table[T] / V_sat
    do_ug_l = voltage_mv * do_sat_ug_l / v_sat

    # Convert to mg/L
    do_mg_l = do_ug_l / 1000.0

    # Clamp to a sane freshwater range
    return max(0.0, min(20.0, do_mg_l))


def read(temp_c: float | None = None):
    """
    Read DO sensor and return dissolved oxygen in mg/L.

    If temp_c is None, we call temp_sensor.read_temp_c() as a dependency.
    If your aggregator already has a temperature reading, it can pass it in
    to avoid re-reading the sensor.
    """
    if temp_c is None:
        temp_c = read_temp_c()

    mv = read_channel_mv(DO_CHANNEL)  # sensor voltage in mV from ADS1115
    do_value = mv_and_temp_to_do_mg_l(mv, temp_c)

    return {
        "sensor": "dissolved_oxygen",
        # "value": round(do_value, 2),
        "value": mv,
        "units": "mg/L",
        "status": "ok",
        "temperature_c": round(temp_c, 2),
        "raw_mv": mv,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
