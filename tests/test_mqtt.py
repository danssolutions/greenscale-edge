import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "greenscale-edge" / \
    "greenscale-edge" / "network" / "mqtt.py"


def load_module():
    """Dynamically import mqtt.py from the project."""
    spec = importlib.util.spec_from_file_location("network.mqtt", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def mqtt():
    """Load the MQTT module once per test."""
    return load_module()


def test_connect_success(mqtt):
    """Connect() should succeed when broker connection works."""
    with patch(
        "paho.mqtt.client.Client.connect",
        return_value=0,
    ) as mock_connect:
        pub = mqtt.MQTTPublisher(host="localhost", topic="greenscale/test")
        assert pub.connect() is True
        mock_connect.assert_called_once_with("localhost", 1883, 30)
        assert pub.connected


def test_connect_failure_retries(mqtt):
    """Connect() should retry and fail gracefully after max attempts."""
    with patch(
        "paho.mqtt.client.Client.connect",
        side_effect=Exception("fail"),
    ):
        pub = mqtt.MQTTPublisher(host="localhost", topic="greenscale/test")
        result = pub.connect(retries=2, delay=0)
        assert not result
        assert not pub.connected


def test_publish_json_success(mqtt):
    """Publish should JSON-encode payload and call client.publish()."""
    fake_client = MagicMock()
    pub = mqtt.MQTTPublisher(host="broker", topic="greenscale/test")
    pub.client = fake_client
    pub.connected = True

    payload = {"foo": "bar"}
    result = pub.publish(payload)

    fake_client.publish.assert_called_once()
    args, kwargs = fake_client.publish.call_args
    assert args[0] == "greenscale/test"
    json.loads(args[1])  # must be valid JSON
    assert result is True


def test_publish_triggers_connect_on_first_use(mqtt):
    """If not connected, publish() should attempt to connect first."""
    with (
        patch.object(mqtt.MQTTPublisher, "connect", return_value=True)
        as mock_connect,
        patch("paho.mqtt.client.Client.publish", return_value=True)
        as mock_pub,
    ):

        pub = mqtt.MQTTPublisher(host="broker", topic="greenscale/test")
        payload = {"key": "value"}
        result = pub.publish(payload)

        mock_connect.assert_called_once()
        mock_pub.assert_called_once()
        assert result is True


def test_publish_handles_failure_and_resets_connection(mqtt):
    """If publish raises, connection flag should reset to False."""
    fake_client = MagicMock()
    fake_client.publish.side_effect = Exception("Network error")

    pub = mqtt.MQTTPublisher(host="broker", topic="greenscale/test")
    pub.client = fake_client
    pub.connected = True

    result = pub.publish({"data": 123})
    assert result is False
    assert not pub.connected


def test_connect_with_tls_configuration(mqtt):
    """TLS parameters should be wired to the MQTT client when enabled."""
    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch("paho.mqtt.client.Client.tls_set") as mock_tls_set,
        patch("paho.mqtt.client.Client.tls_insecure_set") as mock_insecure_set,
        patch("paho.mqtt.client.Client.connect", return_value=0)
        as mock_connect,
    ):

        pub = mqtt.MQTTPublisher(
            host="localhost",
            topic="greenscale/test",
            tls_enable=True,
            ca_cert="/path/ca.pem",
            client_cert="/path/cert.pem",
            client_key="/path/key.pem",
            tls_insecure=True,
        )

        assert pub.connect(retries=1, delay=0)
        mock_tls_set.assert_called_once_with(
            ca_certs="/path/ca.pem",
            certfile="/path/cert.pem",
            keyfile="/path/key.pem",
        )
        mock_insecure_set.assert_called_once_with(True)
        mock_connect.assert_called_once_with("localhost", 1883, 30)


def test_connect_with_missing_tls_file(mqtt):
    """Connection should fail if TLS is enabled but files are missing."""
    with (
        patch("pathlib.Path.is_file", return_value=False),
        patch("paho.mqtt.client.Client.connect") as mock_connect,
    ):

        pub = mqtt.MQTTPublisher(
            host="localhost",
            topic="greenscale/test",
            tls_enable=True,
            ca_cert="/missing/ca.pem",
        )

        result = pub.connect(retries=1, delay=0)
        assert result is False
        mock_connect.assert_not_called()
