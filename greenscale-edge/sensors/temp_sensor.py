DUMMY_TEMP = {
    "sensor": "temperature",
    "value": 22.5,
    "units": "degC",
    "status": "ok",
    "timestamp": "2024-01-01T00:00:00Z",
}


def read():
    """Return a deterministic temperature reading."""
    return dict(DUMMY_TEMP)
