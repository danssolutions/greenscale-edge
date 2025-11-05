import random
from datetime import datetime


def read():
    """Simulate temperature sensor reading in degrees Celsius."""
    return {
        "sensor": "temperature",
        "value": round(22.0 + random.uniform(-0.4, 0.4), 2),
        "units": "degC",
        "status": "ok",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
