DUMMY_DO = {
    "sensor": "dissolved_oxygen",
    "value": 7.5,
    "units": "mg/L",
    "status": "ok",
    "timestamp": "2024-01-01T00:00:00Z",
}


def read():
    """Return a deterministic DO reading."""
    return dict(DUMMY_DO)
