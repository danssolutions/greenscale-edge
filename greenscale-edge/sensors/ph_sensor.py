import random
from datetime import datetime


def read():
    """Simulate pH sensor reading."""
    return {
        "sensor": "ph",
        "value": round(7.0 + random.uniform(-0.1, 0.1), 2),
        "units": "pH",
        "status": "ok",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
