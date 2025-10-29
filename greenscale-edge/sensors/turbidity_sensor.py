DUMMY_TURBIDITY = {
    "sensor": "turbidity",
    "value": 1.2,
    "units": "NTU",
    "status": "ok",
    "timestamp": "2024-01-01T00:00:00Z",
}


def read():
    """Return a deterministic turbidity reading."""
    return dict(DUMMY_TURBIDITY)
