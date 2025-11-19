# sensors/adc.py
"""
Thin wrapper around the vendored DFRobot ADS1115 driver.

A0 -> turbidity
A1 -> pH
A2 -> DO
"""

from .DFRobot_ADS1115 import ADS1115

# DFRobot gain constants
ADS1115_REG_CONFIG_PGA_6_144V = 0x00  # 6.144V range = Gain 2/3

_adc = ADS1115()
_adc.set_addr_ADS1115(0x48)
_adc.set_gain(ADS1115_REG_CONFIG_PGA_6_144V)


def read_channel_mv(channel: int) -> float:
    """Read a channel and return millivolts as float."""
    val = _adc.read_voltage(channel)   # {'r': <millivolts>}
    return float(val["r"])
