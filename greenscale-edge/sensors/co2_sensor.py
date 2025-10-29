DUMMY_CO2 = {
    "sensor": "co2",
    "value": 415.2,
    "units": "ppm",
    "status": "ok",
    "timestamp": "2024-01-01T00:00:00Z",
}


def read():
    """Return a deterministic CO₂ reading."""
    return dict(DUMMY_CO2)
