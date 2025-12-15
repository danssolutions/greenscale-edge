import importlib.util
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "greenscale-edge" / \
    "greenscale-edge" / "camera" / "camera.py"
PROJECT_SRC = REPO_ROOT / "greenscale-edge" / "greenscale-edge"


@pytest.fixture
def camera_module(monkeypatch):
    """Dynamically load the camera module for testing."""
    monkeypatch.syspath_prepend(str(PROJECT_SRC))

    dummy_cv2 = types.SimpleNamespace(
        COLOR_RGB2GRAY=0,
        COLOR_RGB2BGR=1,
        resize=lambda *_, **__: None,
        cvtColor=lambda *_, **__: None,
        imwrite=lambda *_, **__: None,
    )
    dummy_picamera2 = types.SimpleNamespace(Picamera2=lambda *_, **__: None)

    monkeypatch.setitem(sys.modules, "cv2", dummy_cv2)
    monkeypatch.setitem(sys.modules, "picamera2", dummy_picamera2)

    spec = importlib.util.spec_from_file_location("camera.camera", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_compute_camera_metrics_uses_average_and_turbidity(monkeypatch, camera_module):
    """compute_camera_metrics should return RGB hex and turbidity index."""

    class ResizedFrame:
        def __init__(self, data):
            self.data = data

        def reshape(self, *_):
            return self

        def mean(self, axis=None):
            if axis != 0:
                raise ValueError("Unsupported axis")
            pixels = [pixel for row in self.data for pixel in row]
            channel_count = len(pixels[0])
            return [
                sum(p[i] for p in pixels) / len(pixels)
                for i in range(channel_count)
            ]

    class GrayFrame:
        def __init__(self, values):
            self.values = values

        def std(self):
            flattened = [v for row in self.values for v in row]
            mean = sum(flattened) / len(flattened)
            variance = sum((v - mean) ** 2 for v in flattened) / len(flattened)
            return variance**0.5

    resized_frame = ResizedFrame(
        [
            [[10, 20, 30], [110, 120, 130]],
            [[210, 220, 230], [250, 240, 230]],
        ]
    )
    expected_avg = resized_frame.mean(axis=0)
    expected_hex = f"#{int(expected_avg[0]):02x}{int(expected_avg[1]):02x}{int(expected_avg[2]):02x}"

    gray_frame = GrayFrame([[0, 64], [128, 255]])
    expected_std = float(gray_frame.std())
    normalized_std = max(0.0, min(expected_std / 64.0, 1.0))
    expected_turbidity = 1.0 - normalized_std

    monkeypatch.setattr(camera_module, "_capture_raw_frame",
                        lambda: [[0, 0, 0]])
    monkeypatch.setattr(camera_module.cv2, "resize",
                        lambda frame, size: resized_frame)
    monkeypatch.setattr(camera_module.cv2, "cvtColor",
                        lambda frame, code: gray_frame)

    metrics = camera_module.compute_camera_metrics()

    assert metrics["avg_color_hex"] == expected_hex
    assert pytest.approx(metrics["turbidity_index"],
                         rel=1e-3) == expected_turbidity


def test_capture_snapshot_writes_file(monkeypatch, tmp_path, camera_module):
    """capture_snapshot should write a PNG file to SNAPSHOT_DIR."""
    fake_frame = [[[255 for _ in range(3)]
                   for _ in range(3)] for _ in range(3)]
    converted_frame = [[[0 for _ in range(3)]
                        for _ in range(3)] for _ in range(3)]

    monkeypatch.setattr(camera_module, "SNAPSHOT_DIR", tmp_path)
    monkeypatch.setattr(
        camera_module, "_capture_raw_frame", lambda: fake_frame)
    monkeypatch.setattr(camera_module.cv2, "cvtColor",
                        lambda frame, code: converted_frame)

    imwrite_calls = []

    def fake_imwrite(path, data):
        imwrite_calls.append((path, data.copy()))
        return True

    monkeypatch.setattr(camera_module.cv2, "imwrite", fake_imwrite)

    output_path = camera_module.capture_snapshot()

    assert output_path.parent == tmp_path
    assert output_path.suffix == ".png"
    assert output_path.name.startswith("snapshot_")
    assert len(imwrite_calls) == 1
    written_path, written_data = imwrite_calls[0]
    assert written_path == str(output_path)
    assert written_data == converted_frame
