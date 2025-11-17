import json
import time
from pathlib import Path

import paho.mqtt.client as mqtt


class MQTTPublisher:
    """Handles MQTT connection and message publishing."""

    def __init__(
        self,
        host,
        topic,
        port=1883,
        keepalive=30,
        tls_enable=False,
        ca_cert=None,
        client_cert=None,
        client_key=None,
        tls_insecure=False,
    ):
        self.host = host
        self.port = port
        self.topic = topic
        self.keepalive = keepalive
        self.tls_enable = tls_enable
        self.ca_cert = ca_cert
        self.client_cert = client_cert
        self.client_key = client_key
        self.tls_insecure = tls_insecure
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.connected = False

    def _validate_tls_files(self):
        """Ensure provided TLS file paths exist."""
        for label, path in (
            ("CA certificate", self.ca_cert),
            ("client certificate", self.client_cert),
            ("client key", self.client_key),
        ):
            if path and not Path(path).is_file():
                raise FileNotFoundError(f"{label} not found: {path}")

    def _configure_tls(self):
        """Configure TLS settings on the MQTT client if enabled."""
        if not self.tls_enable:
            return

        self._validate_tls_files()
        self.client.tls_set(
            ca_certs=self.ca_cert,
            certfile=self.client_cert,
            keyfile=self.client_key,
        )
        if self.tls_insecure:
            self.client.tls_insecure_set(True)

    def connect(self, retries=3, delay=2):
        """Connect to the MQTT broker, retrying a few times if needed."""
        for attempt in range(retries):
            try:
                self._configure_tls()
                self.client.connect(self.host, self.port, self.keepalive)
                self.client.loop_start()
                self.connected = True
                tls_status = " with TLS" if self.tls_enable else ""
                message = (
                    f"[MQTT] Connected to {self.host}:{self.port}{tls_status}")
                print(message)
                return True
            except Exception as e:
                print(
                    f"[WARN] MQTT connect failed ({attempt+1}/{retries}): {e}")
                time.sleep(delay)
        print("[ERROR] MQTT: could not connect.")
        return False

    def publish(self, payload, qos=1):
        """Publish a JSON payload to the configured topic."""
        if not self.connected and not self.connect():
            print("[ERROR] MQTT publish skipped (no connection).")
            return False

        try:
            message = json.dumps(payload)
            self.client.publish(self.topic, message, qos=qos)
            print(f"[MQTT] Published to {self.topic}")
            return True
        except Exception as e:
            print(f"[ERROR] MQTT publish failed: {e}")
            self.connected = False
            return False
