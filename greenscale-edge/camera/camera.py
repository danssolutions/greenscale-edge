#!/usr/bin/env python3

"""Camera utilities for the Greenscale edge device.

- capture_snapshot(): capture an image and save it to disk (debug/manual use)
- compute_camera_metrics(): capture an image and compute:
    * avg_color_hex: average color in #RRGGBB
    * turbidity_index: heuristic turbidity estimate in [0.0, 1.0]

The turbidity estimate is based on image contrast:
- Clear water (high contrast) → lower turbidity_index
- Cloudy water (low contrast, more uniform) → higher turbidity_index
"""

import datetime
from pathlib import Path
import time

import cv2
from picamera2 import Picamera2

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "snapshots"


def _capture_raw_frame(size=(1280, 720)):
    """
    Capture a single frame from the Pi camera and return it as an RGB ndarray.

    The resolution (default 1280x720) is supported by both V2 and V3 camera modules
    and is a reasonable compromise between speed and detail.
    """
    picam2 = Picamera2()
    configuration = picam2.create_still_configuration(main={"size": size})
    picam2.configure(configuration)
    picam2.start()

    # Give the sensor a short amount of time to collect exposure data
    time.sleep(0.5)
    frame = picam2.capture_array()
    picam2.stop()

    if frame is None:
        raise RuntimeError("Failed to capture image from camera")

    # Picamera2 gives RGB by default; no channel swap needed here
    return frame


def compute_camera_metrics():
    """
    Capture a frame and compute average color + a simple turbidity index.

    Returns:
        dict with:
            - "avg_color_hex": string, e.g. "#58a45e"
            - "turbidity_index": float in [0.0, 1.0]
    """
    frame = _capture_raw_frame()

    # Downscale for faster processing – we don't need full resolution
    resized = cv2.resize(frame, (320, 180))

    # === Average color (RGB) ===
    # Compute mean across all pixels in the downscaled image
    avg_rgb = resized.reshape(-1, 3).mean(axis=0)
    r, g, b = [int(round(v)) for v in avg_rgb]
    avg_color_hex = f"#{r:02x}{g:02x}{b:02x}"

    # === Turbidity heuristic ===
    # Idea:
    #   - Convert to grayscale
    #   - Compute standard deviation of intensities (image contrast)
    #   - High contrast -> clear water -> low turbidity_index
    #   - Low contrast  -> cloudy water -> high turbidity_index
    gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
    std_intensity = float(gray.std())

    # Normalize std deviation to ~[0, 1] using a typical contrast scale
    # The divisor (64.0) is arbitrary and may need tuning/calibration.
    normalized_std = std_intensity / 64.0
    normalized_std = max(0.0, min(normalized_std, 1.0))

    turbidity_index = 1.0 - normalized_std

    return {
        "avg_color_hex": avg_color_hex,
        "turbidity_index": turbidity_index,
    }


def capture_snapshot() -> Path:
    """Capture a frame and write it to the snapshots directory (for debugging)."""

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = SNAPSHOT_DIR / f"snapshot_{timestamp}.png"

    frame = _capture_raw_frame(size=(4608, 2592))

    # For saving with OpenCV we need BGR order
    bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    if not cv2.imwrite(str(file_path), bgr_frame):
        raise RuntimeError(f"Failed to write snapshot to {file_path}")

    return file_path


if __name__ == "__main__":
    # Manual test: compute metrics and also save a debug snapshot
    metrics = compute_camera_metrics()
    path = capture_snapshot()
    print(f"Snapshot saved to {path}")
    print(f"Camera metrics: {metrics}")
