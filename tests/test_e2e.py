import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_SRC = REPO_ROOT / "greenscale-edge" / "greenscale-edge"
MAIN_MODULE_PATH = PROJECT_SRC / "main.py"

if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))


def load_main_module(env, module_name="greenscale_edge_e2e_main"):
    """Load a fresh instance of main.py with provided environment overrides."""
    spec = importlib.util.spec_from_file_location(
        module_name, MAIN_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    with env:
        spec.loader.exec_module(module)
    return module


def test_main_runs_single_cycle_end_to_end(
    deterministic_environment, deterministic_sensors, monkeypatch
):
    """Run main() once end-to-end and inspect the broker payload."""
    config_data = {"broker_host": "localhost", "publish_interval": 0}
    env = deterministic_environment.set_env(
        config_data, device_id="e2e-device")

    import network.mqtt as mqtt_module

    original_publish = mqtt_module.MQTTPublisher.publish
    captured_publishers = []

    def publish_and_stop(self, payload, qos=1):
        captured_publishers.append(self)
        result = original_publish(self, payload, qos)
        raise KeyboardInterrupt()

    monkeypatch.setattr(mqtt_module.MQTTPublisher, "publish", publish_and_stop)

    main = load_main_module(env)
    main.main()

    assert captured_publishers, "MQTT publisher should be invoked"
    published = captured_publishers[-1].client.published_messages[-1]
    decoded = json.loads(published["payload"])

    assert decoded["device_id"] == "e2e-device"
    assert decoded["sensors"]["temperature_c"] == 19.8
    assert decoded["camera"]["avg_color_hex"] == "#123456"
    assert published["topic"].endswith("/telemetry")
