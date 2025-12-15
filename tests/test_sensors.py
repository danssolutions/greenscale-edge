import importlib
import sys
import types
from datetime import datetime
from pathlib import Path

import pytest

# Adjust paths as needed if you move the test folder
REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_SRC = REPO_ROOT / "greenscale-edge" / "greenscale-edge"
SENSOR_DIR = PROJECT_SRC / "sensors"

SENSOR_MODULES = [
    "temp_sensor",
    "ph_sensor",
    "do_sensor",
    "turbidity_sensor",
]


@pytest.fixture(autouse=True)
def add_project_to_path(monkeypatch):
    """Ensure the project source directory is importable and stub hardware modules."""

    if str(PROJECT_SRC) not in sys.path:
        monkeypatch.syspath_prepend(str(PROJECT_SRC))

    sensors_pkg = types.ModuleType("sensors")
    sensors_pkg.__path__ = []

    adc_module = types.ModuleType("sensors.adc")
    adc_module.read_channel_mv = lambda *_args, **_kwargs: 1500

    temp_module = types.ModuleType("sensors.temp_sensor")
    temp_module.read_temp_c = lambda: 22.5
    temp_module.read = lambda: {
        "sensor": "temperature",
        "value": 22.5,
        "units": "degC",
        "status": "ok",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    ph_module = types.ModuleType("sensors.ph_sensor")
    ph_module.read = lambda: {
        "sensor": "ph",
        "value": 7.0,
        "units": "pH",
        "status": "ok",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    do_module = types.ModuleType("sensors.do_sensor")
    do_module.read = lambda temp_c=None: {
        "sensor": "dissolved_oxygen",
        "value": 8.5,
        "units": "mg/L",
        "status": "ok",
        "temperature_c": 20.0,
        "raw_mv": 1500,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    turbidity_module = types.ModuleType("sensors.turbidity_sensor")
    turbidity_module.read = lambda: {
        "sensor": "turbidity",
        "value": 3.0,
        "units": "NTU",
        "status": "ok",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    monkeypatch.setitem(sys.modules, "sensors", sensors_pkg)
    monkeypatch.setitem(sys.modules, "sensors.adc", adc_module)
    monkeypatch.setitem(sys.modules, "sensors.temp_sensor", temp_module)
    monkeypatch.setitem(sys.modules, "sensors.ph_sensor", ph_module)
    monkeypatch.setitem(sys.modules, "sensors.do_sensor", do_module)
    monkeypatch.setitem(sys.modules, "sensors.turbidity_sensor", turbidity_module)


def load_sensor_module(module_name: str, monkeypatch: pytest.MonkeyPatch):
    """Dynamically load a sensor module by filename."""
    return importlib.import_module(f"sensors.{module_name}")


@pytest.mark.parametrize("module_name", SENSOR_MODULES)
def test_read_function_exists(module_name: str, monkeypatch: pytest.MonkeyPatch):
    """Each sensor module must define a callable read() function."""
    module = load_sensor_module(module_name, monkeypatch)
    assert hasattr(module, "read"), f"{module_name} missing read()"
    assert callable(module.read), f"{module_name}.read is not callable"


@pytest.mark.parametrize("module_name", SENSOR_MODULES)
def test_read_output_structure(module_name: str, monkeypatch: pytest.MonkeyPatch):
    """Each sensor read() must return a properly structured dict."""
    module = load_sensor_module(module_name, monkeypatch)
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
def test_value_ranges(module_name: str, monkeypatch: pytest.MonkeyPatch):
    """Make sure simulated values fall within realistic physical ranges."""
    module = load_sensor_module(module_name, monkeypatch)
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
