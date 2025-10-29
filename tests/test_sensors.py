import importlib.util
from pathlib import Path
from typing import Dict

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SENSOR_DIR = REPO_ROOT / "greenscale-edge" / "greenscale-edge" / "sensors"

SENSOR_LIST: Dict[str, object] = {
    "ammonia_sensor":
    {
        "sensor": "ammonia",
        "value": 0.25,
        "units": "ppm",
        "status": "ok",
        "timestamp": "2024-01-01T00:00:00Z",
    },
    "co2_sensor":
    {
        "sensor": "co2",
        "value": 415.2,
        "units": "ppm",
        "status": "ok",
        "timestamp": "2024-01-01T00:00:00Z",
    },
    "do_sensor":
    {
        "sensor": "dissolved_oxygen",
        "value": 7.5,
        "units": "mg/L",
        "status": "ok",
        "timestamp": "2024-01-01T00:00:00Z",
    },
    "ph_sensor":
    {
        "sensor": "ph",
        "value": 7.0,
        "units": "pH",
        "status": "ok",
        "timestamp": "2024-01-01T00:00:00Z",
    },
    "temp_sensor":
    {
        "sensor": "temperature",
        "value": 22.5,
        "units": "degC",
        "status": "ok",
        "timestamp": "2024-01-01T00:00:00Z",
    },
    "turbidity_sensor":
    {
        "sensor": "turbidity",
        "value": 1.2,
        "units": "NTU",
        "status": "ok",
        "timestamp": "2024-01-01T00:00:00Z",
    },
}


def load_sensor_module(module_name: str):
    file_path = SENSOR_DIR / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(
        f"test_{module_name}", file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("module_name", SENSOR_LIST.keys())
def test_reading_matches_expected(module_name: str):
    module = load_sensor_module(module_name)
    expected_reading = SENSOR_LIST[module_name]
    reading = module.read()
    # TODO: update test when real sensor reading implemented
    assert reading == expected_reading
