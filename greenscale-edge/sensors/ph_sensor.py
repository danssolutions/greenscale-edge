DUMMY_PH = {
    "sensor": "ph",
    "value": 7.0,
    "units": "pH",
    "status": "ok",
    "timestamp": "2024-01-01T00:00:00Z",
}


def read():
    """Return a deterministic pH reading."""
    return dict(DUMMY_PH)
