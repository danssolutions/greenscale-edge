import importlib.util
from pathlib import Path
from datetime import datetime

import pytest

# Adjust paths as needed if you move the test folder
REPO_ROOT = Path(__file__).resolve().parents[2]
SENSOR_DIR = REPO_ROOT / "greenscale-edge" / "greenscale-edge" / "sensors"

SENSOR_MODULES = [
    "temp_sensor",
    "ph_sensor",
    "do_sensor",
    "turbidity_sensor",
]


def load_sensor_module(module_name: str):
    """Dynamically load a sensor module by filename."""
    file_path = SENSOR_DIR / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("module_name", SENSOR_MODULES)
def test_read_function_exists(module_name: str):
    """Each sensor module must define a callable read() function."""
    module = load_sensor_module(module_name)
    assert hasattr(module, "read"), f"{module_name} missing read()"
    assert callable(module.read), f"{module_name}.read is not callable"


@pytest.mark.parametrize("module_name", SENSOR_MODULES)
def test_read_output_structure(module_name: str):
    """Each sensor read() must return a properly structured dict."""
    module = load_sensor_module(module_name)
    reading = module.read()

    # Validate required keys
    expected_keys = {"sensor", "value", "units", "status", "timestamp"}
    assert isinstance(reading, dict)
    assert expected_keys.issubset(
        reading.keys()), f"{module_name} missing required keys"

    # Validate data types
    assert isinstance(reading["sensor"], str)
    assert isinstance(reading["value"], (int, float))
    assert isinstance(reading["units"], str)
    assert isinstance(reading["status"], str)
    assert isinstance(reading["timestamp"], str)

    # Validate timestamp format (ISO 8601)
    try:
        datetime.strptime(reading["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        pytest.fail(f"{module_name} timestamp not in ISO 8601 format")


@pytest.mark.parametrize("module_name", SENSOR_MODULES)
def test_value_ranges(module_name: str):
    """Make sure simulated values fall within realistic physical ranges."""
    module = load_sensor_module(module_name)
    reading = module.read()
    v = reading["value"]

    if module_name == "temp_sensor":
        assert 0 <= v <= 40
    elif module_name == "ph_sensor":
        assert 0 <= v <= 14
    elif module_name == "do_sensor":
        assert 0 <= v <= 15
    elif module_name == "turbidity_sensor":
        assert 0 <= v <= 10
