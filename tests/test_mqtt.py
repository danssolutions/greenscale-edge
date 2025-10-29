import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "greenscale-edge" / \
    "greenscale-edge" / "network" / "mqtt.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "greenscale_edge.network.mqtt", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="mqtt")
def mqtt_module():
    return load_module()


def test_collect_sensor_readings_uses_stub_values(mqtt):
    readings = mqtt.collect_sensor_readings()
    sensor_names = {reading["sensor"] for reading in readings}

    assert sensor_names == {
        "ammonia",
        "co2",
        "dissolved_oxygen",
        "ph",
        "temperature",
        "turbidity",
    }


def test_build_sensor_message_combines_data(mqtt):
    readings = [
        {"sensor": "temperature", "value": 22.5},
        {"sensor": "ph", "value": 7.0},
    ]
    camera_metadata = {"file": "snapshot.png", "exposure": 0.1}

    payload = mqtt.build_sensor_message(
        readings, camera_metadata, site="pond-1")

    assert payload["sensors"] == readings
    assert payload["camera"] == camera_metadata
    assert payload["site"] == "pond-1"
    # Ensure the payload is ready for publishing as JSON
    json.dumps(payload)


def test_publish_attempts_to_connect_and_publishes_json(mqtt):
    client = MagicMock()
    publisher = mqtt.MQTTPublisher(
        topic="greenscale/sensors",
        host="mqtt.local",
        port=1884,
        client=client,
        reconnect_delay=0,
    )

    payload = {"sensors": [{"sensor": "temperature", "value": 22.5}]}
    publisher.publish(payload)

    client.connect.assert_called_once_with("mqtt.local", 1884, 60)
    assert client.publish.call_count == 1
    args, kwargs = client.publish.call_args
    assert args[0] == "greenscale/sensors"
    message = json.loads(args[1])
    assert message == payload
    assert kwargs == {"qos": 0, "retain": False}


def test_publish_reconnects_after_failure(mqtt):
    client = MagicMock()
    fail = RuntimeError("network error")
    sentinel = object()
    client.publish.side_effect = [fail, sentinel, sentinel]

    publisher = mqtt.MQTTPublisher(
        topic="greenscale/sensors",
        client=client,
        reconnect_delay=0,
        max_retries=2,
    )

    result = publisher.publish({"foo": "bar"})

    assert client.connect.call_count == 2
    assert client.publish.call_count == 2
    assert result is sentinel
    # Subsequent publishes should reuse the existing connection
    publisher.publish({"foo": "baz"})
    assert client.connect.call_count == 2
