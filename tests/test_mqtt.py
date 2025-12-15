import datetime
import importlib.util
import importlib
import json
import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "greenscale-edge" / \
    "greenscale-edge" / "network" / "mqtt.py"
MAIN_MODULE_PATH = REPO_ROOT / "greenscale-edge" / \
    "greenscale-edge" / "main.py"
PROJECT_SRC = REPO_ROOT / "greenscale-edge" / "greenscale-edge"

if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))


@pytest.fixture(autouse=True)
def stub_paho(monkeypatch):
    """Provide a lightweight stub for paho-mqtt so tests run without the package."""

    class FakeClient:
        def __init__(self, *_, **__):
            self._username = None
            self._password = None

        def connect(self, *_args, **_kwargs):
            return 0

        def publish(self, *_args, **_kwargs):
            return True

        def username_pw_set(self, username, password):
            self._username = username
            self._password = password

        def tls_set(self, *_, **__):
            return True

        def tls_insecure_set(self, *_args, **_kwargs):
            return True

        def loop_start(self):
            return True

    class _CallbackAPIVersion:
        VERSION1 = 1
        VERSION2 = 2

    cv2_mod = types.ModuleType("cv2")
    cv2_mod.COLOR_RGB2GRAY = 0
    cv2_mod.COLOR_RGB2BGR = 1
    cv2_mod.resize = lambda img, size: img
    cv2_mod.cvtColor = lambda img, code: img
    cv2_mod.imwrite = lambda path, frame: True

    picam_mod = types.ModuleType("picamera2")

    class FakePicamera2:
        def __init__(self):
            self.started = False

        def start(self):
            self.started = True

        def stop(self):
            self.started = False

        def capture_array(self, *_args, **_kwargs):
            return [[0, 0, 0]]

    picam_mod.Picamera2 = FakePicamera2

    sensors_pkg = types.ModuleType("sensors")
    sensors_pkg.__path__ = []
    sensors_pkg.__all__ = [
        "temp_sensor",
        "ph_sensor",
        "do_sensor",
        "turbidity_sensor",
    ]

    temp_module = types.ModuleType("sensors.temp_sensor")
    temp_module.read = lambda: {
        "sensor": "temperature",
        "value": 22.5,
        "units": "degC",
        "status": "ok",
        "timestamp": datetime.datetime.now(datetime.UTC).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    }

    ph_module = types.ModuleType("sensors.ph_sensor")
    ph_module.read = lambda: {
        "sensor": "ph",
        "value": 7.0,
        "units": "pH",
        "status": "ok",
        "timestamp": datetime.datetime.now(datetime.UTC).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    }

    do_module = types.ModuleType("sensors.do_sensor")
    do_module.read = lambda: {
        "sensor": "dissolved_oxygen",
        "value": 8.5,
        "units": "mg/L",
        "status": "ok",
        "temperature_c": 20.0,
        "raw_mv": 1500,
        "timestamp": datetime.datetime.now(datetime.UTC).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    }

    turbidity_module = types.ModuleType("sensors.turbidity_sensor")
    turbidity_module.read = lambda: {
        "sensor": "turbidity",
        "value": 3.0,
        "units": "NTU",
        "status": "ok",
        "timestamp": datetime.datetime.now(datetime.UTC).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    }

    paho_mod = types.ModuleType("paho")
    mqtt_mod = types.ModuleType("paho.mqtt")
    client_mod = types.ModuleType("paho.mqtt.client")
    client_mod.Client = FakeClient
    client_mod.CallbackAPIVersion = _CallbackAPIVersion
    mqtt_mod.client = client_mod
    paho_mod.mqtt = mqtt_mod

    monkeypatch.setitem(sys.modules, "paho", paho_mod)
    monkeypatch.setitem(sys.modules, "paho.mqtt", mqtt_mod)
    monkeypatch.setitem(sys.modules, "paho.mqtt.client", client_mod)
    monkeypatch.setitem(sys.modules, "cv2", cv2_mod)
    monkeypatch.setitem(sys.modules, "picamera2", picam_mod)
    monkeypatch.setitem(sys.modules, "sensors", sensors_pkg)
    monkeypatch.setitem(sys.modules, "sensors.temp_sensor", temp_module)
    monkeypatch.setitem(sys.modules, "sensors.ph_sensor", ph_module)
    monkeypatch.setitem(sys.modules, "sensors.do_sensor", do_module)
    monkeypatch.setitem(sys.modules, "sensors.turbidity_sensor", turbidity_module)
    sensors_pkg.temp_sensor = temp_module
    sensors_pkg.ph_sensor = ph_module
    sensors_pkg.do_sensor = do_module
    sensors_pkg.turbidity_sensor = turbidity_module


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


def test_connect_with_credentials_sets_username_and_password(mqtt):
    """Username/password should be applied before connecting."""
    with (
        patch("paho.mqtt.client.Client.username_pw_set") as mock_auth,
        patch("paho.mqtt.client.Client.connect", return_value=0)
        as mock_connect,
    ):

        pub = mqtt.MQTTPublisher(
            host="localhost",
            topic="greenscale/test",
            username="user1",
            password="secret",
        )

        assert pub.connect(retries=1, delay=0)
        mock_auth.assert_called_once_with("user1", "secret")
        mock_connect.assert_called_once_with("localhost", 1883, 30)


def test_main_passes_configured_credentials_to_publisher(tmp_path):
    """main() should construct publisher with configured credentials."""
    config_data = {
        "broker_host": "example.org",
        "publish_interval": 1,
        "broker_username": "alice",
        "broker_password": "wonderland",
        "broker_port": 8883,
        "tls_enable": True,
        "tls_ca_cert": "/etc/ssl/certs/ca.pem",
        "tls_client_cert": "/etc/ssl/certs/client.pem",
        "tls_client_key": "/etc/ssl/private/client.key",
        "tls_insecure": False,
    }
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps(config_data))

    with (
        patch.dict(os.environ, {"CONFIG_PATH": str(cfg_file)}),
        patch("network.mqtt.MQTTPublisher") as mock_pub_cls,
        patch("time.sleep", return_value=None),
    ):
        mock_instance = MagicMock()
        mock_instance.connect.return_value = True
        mock_instance.publish.side_effect = KeyboardInterrupt()
        mock_pub_cls.return_value = mock_instance

        spec = importlib.util.spec_from_file_location(
            "greenscale_edge_main_test", MAIN_MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        module.main()

        mock_pub_cls.assert_called_with(
            config_data["broker_host"],
            module.TOPIC,
            port=config_data["broker_port"],
            tls_enable=config_data["tls_enable"],
            ca_cert=config_data["tls_ca_cert"],
            client_cert=config_data["tls_client_cert"],
            client_key=config_data["tls_client_key"],
            tls_insecure=config_data["tls_insecure"],
            username=config_data["broker_username"],
            password=config_data["broker_password"],
        )


def test_load_config_applies_security_defaults(tmp_path):
    """Missing security settings should fall back to safe defaults."""
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({"broker_host": "secure.example"}))

    with patch.dict(os.environ, {"CONFIG_PATH": str(cfg_file)}):
        spec = importlib.util.spec_from_file_location(
            "greenscale_edge_config_test", MAIN_MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        config = module.load_config()

    assert config["broker_host"] == "secure.example"
    assert config["broker_port"] == 1883
    assert config["tls_enable"] is False
    assert config["tls_ca_cert"] is None
    assert config["tls_client_cert"] is None
    assert config["tls_client_key"] is None
    assert config["tls_insecure"] is False
