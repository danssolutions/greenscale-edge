import os
import socket
import time
from datetime import datetime, UTC
from network.mqtt import MQTTPublisher
from sensors import temp_sensor, ph_sensor, do_sensor, turbidity_sensor
import json
import pathlib


CFG_PATH = pathlib.Path(os.environ.get(
    "CONFIG_PATH",
    "/home/user/greenscale-edge/greenscale-edge/config.json",
))


def load_config():
    if CFG_PATH.exists():
        with CFG_PATH.open() as f:
            return json.load(f)
    return {
        "broker_host": "192.168.1.100",
        "publish_interval": 10,
        "broker_username": None,
        "broker_password": None,
    }


cfg = load_config()
BROKER_HOST = cfg.get("broker_host", "192.168.1.100")
BROKER_USERNAME = cfg.get("broker_username")
BROKER_PASSWORD = cfg.get("broker_password")
PUBLISH_INTERVAL = cfg.get("publish_interval", 10)
DEVICE_ID = os.getenv("DEVICE_ID", socket.gethostname())
TOPIC = f"greenscale/{DEVICE_ID}/telemetry"


# === Data Collection ===
def collect_sensor_data():
    """Gather current readings from available sensors."""
    return {
        "temperature_c": temp_sensor.read()["value"],
        "ph": ph_sensor.read()["value"],
        "do_mg_per_l": do_sensor.read()["value"],
        "turbidity_sensor_v": turbidity_sensor.read()["value"],
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
    global cfg
    publisher = MQTTPublisher(
        cfg["broker_host"],
        TOPIC,
        username=cfg.get("broker_username"),
        password=cfg.get("broker_password"),
    )
    publisher.connect()

    print(f"[INFO] Starting Greenscale Edge node '{DEVICE_ID}'")
    last_mtime = 0
    while True:
        try:
            mtime = CFG_PATH.stat().st_mtime
            if mtime != last_mtime:
                cfg = load_config()
                last_mtime = mtime
            sensors = collect_sensor_data()
            camera = collect_camera_data()
            payload = build_payload(sensors, camera)
            publisher.publish(payload)
            time.sleep(cfg["publish_interval"])
        except KeyboardInterrupt:
            print("[INFO] Exiting...")
            break
        except Exception as e:
            print(f"[ERROR] Main loop exception: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
