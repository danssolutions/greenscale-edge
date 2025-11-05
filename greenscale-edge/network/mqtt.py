import json
import time
import paho.mqtt.client as mqtt


class MQTTPublisher:
    """Handles MQTT connection and message publishing."""

    def __init__(self, host, topic, port=1883, keepalive=30):
        self.host = host
        self.port = port
        self.topic = topic
        self.keepalive = keepalive
        self.client = mqtt.Client()
        self.connected = False

    def connect(self, retries=3, delay=2):
        """Connect to the MQTT broker, retrying a few times if needed."""
        for attempt in range(retries):
            try:
                self.client.connect(self.host, self.port, self.keepalive)
                self.client.loop_start()
                self.connected = True
                print(f"[MQTT] Connected to {self.host}:{self.port}")
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
