import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_SRC = REPO_ROOT / "greenscale-edge" / "greenscale-edge"
MAIN_MODULE_PATH = PROJECT_SRC / "main.py"

if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))


def load_main_module(env, module_name="greenscale_edge_integration_main"):
    """Load a fresh instance of main.py with provided environment overrides."""
    spec = importlib.util.spec_from_file_location(
        module_name, MAIN_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    with env:
        spec.loader.exec_module(module)
    return module


def test_collect_and_publish_cycle_integration(
    deterministic_environment, deterministic_sensors
):
    """Exercise sensor collection, payload build, and publish together."""
    env = deterministic_environment.set_env(
        {"broker_host": "localhost"}, device_id="int-device"
    )
    main = load_main_module(env)
    from network.mqtt import MQTTPublisher

    publisher = MQTTPublisher(host="localhost", topic="greenscale/test")
    assert publisher.connect()

    sensor_data = main.collect_sensor_data()
    camera_data = main.collect_camera_data()
    payload = main.build_payload(sensor_data, camera_data)

    assert publisher.publish(payload)
    published = publisher.client.published_messages[-1]
    decoded = json.loads(published["payload"])

    assert decoded["device_id"] == "int-device"
    assert decoded["sensors"] == {
        "temperature_c": 19.8,
        "ph": 6.9,
        "do_mg_per_l": 7.7,
        "turbidity_sensor_v": 2.5,
    }
    assert decoded["camera"] == {
        "turbidity_index": pytest.approx(0.42),
        "avg_color_hex": "#123456",
    }
    assert published["topic"] == "greenscale/test"
