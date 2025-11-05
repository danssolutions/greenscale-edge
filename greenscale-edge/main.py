import os
import socket
import time
from datetime import datetime, UTC
from network.mqtt import MQTTPublisher
from sensors import temp_sensor, ph_sensor, do_sensor, turbidity_sensor

# === Configuration ===
BROKER_HOST = "192.168.1.100"  # Change to your server IP
DEVICE_ID = os.getenv("DEVICE_ID", socket.gethostname())
TOPIC = f"greenscale/{DEVICE_ID}/telemetry"
PUBLISH_INTERVAL = 10  # seconds


# === Data Collection ===
def collect_sensor_data():
    """Gather current readings from available sensors."""
    return {
        "temperature_c": temp_sensor.read(),
        "ph": ph_sensor.read(),
        "do_mg_per_l": do_sensor.read(),
        "turbidity_sensor_v": turbidity_sensor.read(),
    }


def collect_camera_data():
    """Placeholder for camera metrics."""
    # Replace with actual processing later
    return {
        "turbidity_index": 0.42,
        "avg_color_hex": "#58a45e",
    }


def build_payload(sensor_data, camera_data):
    """Build a full MQTT payload matching team schema."""
    return {
        "version": 1,
        "device_id": DEVICE_ID,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": {
            "online": True,
            "uptime_sec": int(time.monotonic()),
        },
        "sensors": sensor_data,
        "camera": camera_data,
    }


# === Main Loop ===
def main():
    publisher = MQTTPublisher(BROKER_HOST, TOPIC)
    publisher.connect()

    print(f"[INFO] Starting Greenscale Edge node '{DEVICE_ID}'")
    while True:
        try:
            sensors = collect_sensor_data()
            camera = collect_camera_data()
            payload = build_payload(sensors, camera)
            publisher.publish(payload)
            time.sleep(PUBLISH_INTERVAL)
        except KeyboardInterrupt:
            print("[INFO] Exiting...")
            break
        except Exception as e:
            print(f"[ERROR] Main loop exception: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
