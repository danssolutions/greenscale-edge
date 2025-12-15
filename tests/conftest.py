import datetime
import json
import sys
import types

import pytest


@pytest.fixture(autouse=True)
def stub_third_party_modules(monkeypatch):
    """Stub hardware and MQTT dependencies for all tests.

    Provides lightweight stand-ins for paho-mqtt, cv2, Picamera2, and the
    hardware sensor modules so tests can import the application without
    requiring physical devices or native libraries.
    """

    class FakeClient:
        instances = []

        def __init__(self, *_, **__):
            self._username = None
            self._password = None
            self.published_messages = []
            FakeClient.instances.append(self)

        def connect(self, *_args, **_kwargs):
            return 0

        def publish(self, topic, payload, qos=0, **_kwargs):
            self.published_messages.append(
                {"topic": topic, "payload": payload, "qos": qos}
            )
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
    monkeypatch.setitem(
        sys.modules, "sensors.turbidity_sensor", turbidity_module)

    sensors_pkg.temp_sensor = temp_module
    sensors_pkg.ph_sensor = ph_module
    sensors_pkg.do_sensor = do_module
    sensors_pkg.turbidity_sensor = turbidity_module


@pytest.fixture
def deterministic_environment(monkeypatch, tmp_path):
    """Context manager to set CONFIG_PATH/DEVICE_ID for a test run."""

    class EnvOverride:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    env = EnvOverride()

    def set_env(config_data=None, device_id="integration-node"):
        cfg_path = tmp_path / "config.json"
        cfg_path.write_text(
            json.dumps(config_data or {"broker_host": "localhost"})
        )
        monkeypatch.setenv("CONFIG_PATH", str(cfg_path))
        monkeypatch.setenv("DEVICE_ID", device_id)
        return env

    env.set_env = set_env
    return env


@pytest.fixture
def deterministic_sensors(monkeypatch):
    """Make sensor and camera readings deterministic for assertions."""
    import sensors.temp_sensor as temp_sensor
    import sensors.ph_sensor as ph_sensor
    import sensors.do_sensor as do_sensor
    import sensors.turbidity_sensor as turbidity_sensor
    from camera import camera as camera_module

    monkeypatch.setattr(
        temp_sensor,
        "read",
        lambda: {
            "sensor": "temperature",
            "value": 19.8,
            "units": "degC",
            "status": "ok",
            "timestamp": "2024-01-01T00:00:00Z",
        },
    )
    monkeypatch.setattr(
        ph_sensor,
        "read",
        lambda: {
            "sensor": "ph",
            "value": 6.9,
            "units": "pH",
            "status": "ok",
            "timestamp": "2024-01-01T00:00:01Z",
        },
    )
    monkeypatch.setattr(
        do_sensor,
        "read",
        lambda temp_c=None: {
            "sensor": "dissolved_oxygen",
            "value": 7.7,
            "units": "mg/L",
            "status": "ok",
            "temperature_c": 21.0,
            "raw_mv": 1400,
            "timestamp": "2024-01-01T00:00:02Z",
        },
    )
    monkeypatch.setattr(
        turbidity_sensor,
        "read",
        lambda: {
            "sensor": "turbidity",
            "value": 2.5,
            "units": "NTU",
            "status": "ok",
            "timestamp": "2024-01-01T00:00:03Z",
        },
    )
    monkeypatch.setattr(
        camera_module,
        "compute_camera_metrics",
        lambda: {"turbidity_index": 0.42, "avg_color_hex": "#123456"},
    )
