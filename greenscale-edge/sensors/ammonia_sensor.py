DUMMY_AMMONIA = {
    "sensor": "ammonia",
    "value": 0.25,
    "units": "ppm",
    "status": "ok",
    "timestamp": "2024-01-01T00:00:00Z",
}


def read():
    """Return a deterministic ammonia reading."""
    return dict(DUMMY_AMMONIA)
