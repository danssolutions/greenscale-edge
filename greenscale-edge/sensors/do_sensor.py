import random
from datetime import datetime, UTC


def read():
    """Simulate dissolved oxygen (DO) reading in mg/L."""
    return {
        "sensor": "dissolved_oxygen",
        "value": round(7.5 + random.uniform(-0.3, 0.3), 2),
        "units": "mg/L",
        "status": "ok",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
