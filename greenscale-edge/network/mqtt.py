import json
import time
import runpy
from pathlib import Path

SENSOR_MODULES = (
    "ammonia_sensor",
    "co2_sensor",
    "do_sensor",
    "ph_sensor",
    "temp_sensor",
    "turbidity_sensor",
)

SENSOR_DIR = Path(__file__).resolve().parents[1] / "sensors"


def collect_sensor_readings(sensor_module_names=None):
    names = sensor_module_names or SENSOR_MODULES
    return [dict(runpy.run_path(str(SENSOR_DIR / f"{name}.py"))["read"]()) for name in names]


def build_sensor_message(sensor_readings, camera_metadata=None, **metadata):
    payload = {"sensors": [dict(reading) for reading in sensor_readings]}
    if camera_metadata is not None:
        payload["camera"] = dict(camera_metadata)
    payload.update(metadata)
    return payload


class MQTTPublisher:
    def __init__(
        self,
        topic,
        host="localhost",
        port=1883,
        *,
        keepalive=60,
        reconnect_delay=1.0,
        max_retries=3,
        client_id=None,
        username=None,
        password=None,
        client=None,
    ):
        if client is None:
            import paho.mqtt.client as paho_mqtt

            client = paho_mqtt.Client(client_id=client_id)
        if username or password:
            client.username_pw_set(username, password)
        self.topic, self.host, self.port, self.keepalive = topic, host, port, keepalive
        self.reconnect_delay, self.max_retries = max(
            0.0, reconnect_delay), max(1, int(max_retries))
        self.client, self.connected = client, False

    def connect(self):
        if self.connected:
            return
        last_error = None
        for attempt in range(self.max_retries):
            try:
                self.client.connect(self.host, self.port, self.keepalive)
                self.connected = True
                return
            except Exception as exc:  # pragma: no cover - triggered via mocks
                last_error = exc
                self.connected = False
                if attempt + 1 < self.max_retries and self.reconnect_delay:
                    time.sleep(self.reconnect_delay)
        raise RuntimeError(
            f"Failed to connect to MQTT broker at {self.host}:{self.port}") from last_error

    def publish(self, payload, *, qos=0, retain=False):
        message = json.dumps(payload)
        self.connect()
        try:
            return self.client.publish(self.topic, message, qos=qos, retain=retain)
        except Exception:
            self.connected = False
            self.connect()
            try:
                return self.client.publish(self.topic, message, qos=qos, retain=retain)
            except Exception as exc:
                self.connected = False
                raise RuntimeError(
                    "Failed to publish MQTT message after reconnecting") from exc

    def publish_sensor_batch(self, sensor_module_names=None, camera_metadata=None, **metadata):
        payload = build_sensor_message(
            collect_sensor_readings(sensor_module_names), camera_metadata, **metadata
        )
        return self.publish(payload)
