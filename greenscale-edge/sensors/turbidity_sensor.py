import random
from datetime import datetime, UTC


def read():
    """Simulate turbidity sensor reading in NTU."""
    return {
        "sensor": "turbidity",
        "value": round(2.4 + random.uniform(-0.2, 0.2), 2),
        "units": "NTU",
        "status": "ok",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
