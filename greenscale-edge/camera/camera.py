#!/usr/bin/env python3
"""
Camera utilities for the Greenscale edge device.

- compute_camera_metrics():
    Capture a frame and compute:
      * avg_color_hex: average color in #RRGGBB (true RGB, matching snapshot)
      * turbidity_index: heuristic turbidity estimate in [0.0, 1.0]

- capture_snapshot():
    Capture a frame and save it as a PNG under the project-level "snapshots"
    directory, returning the Path.

Notes about color:
- Picamera2 delivers the frame as RGB.
- OpenCV's imwrite expects BGR.
- So for saving we must convert RGB -> BGR (swap red/blue).
- For metrics we work directly in RGB so avg_color_hex lines up with the
  *visually correct* snapshot.
"""

import atexit
import datetime
from pathlib import Path
import time

import cv2
from picamera2 import Picamera2

# Directory where snapshots will be saved:
#   .../greenscale-edge/greenscale-edge/snapshots
SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "snapshots"

# Full still resolution for Pi Camera Module 3
FULL_RESOLUTION = (4608, 2592)

# Single shared Picamera2 instance (avoid "device busy" on repeated use)
_picam2 = None


def _shutdown_camera():
    """Stop the global Picamera2 instance when the process exits."""
    global _picam2
    if _picam2 is not None:
        try:
            _picam2.stop()
        except Exception:
            pass
        _picam2 = None


def _init_camera():
    """Initialise the global Picamera2 instance if needed."""
    global _picam2

    if _picam2 is None:
        cam = Picamera2()
        configuration = cam.create_still_configuration(
            main={"size": FULL_RESOLUTION}
        )
        cam.configure(configuration)
        cam.start()

        # Let AE/AWB settle a bit
        time.sleep(0.5)

        _picam2 = cam
        atexit.register(_shutdown_camera)

    return _picam2


def _capture_raw_frame():
    """
    Capture a single frame from the camera.

    Returns:
        numpy.ndarray with shape (H, W, 3) in **RGB** order.
    """
    cam = _init_camera()
    frame = cam.capture_array()

    if frame is None:
        raise RuntimeError("Failed to capture image from camera")

    # Empirically, this array behaves as RGB for you (saving with RGB->BGR
    # swap gives correct colors), so we treat it as RGB everywhere else.
    return frame  # RGB


def compute_camera_metrics():
    """
    Capture a frame and compute average color + a simple turbidity index.

    Returns:
        dict:
          - "avg_color_hex": string, e.g. "#58a45e"
          - "turbidity_index": float in [0.0, 1.0]
    """
    frame_rgb = _capture_raw_frame()

    # ---- Average color (RGB) ----
    # Downscale for speed; we don't need full 12MP for an average.
    resized = cv2.resize(frame_rgb, (320, 180))
    avg_rgb = resized.reshape(-1, 3).mean(axis=0)
    r, g, b = [int(round(v)) for v in avg_rgb]
    avg_color_hex = f"#{r:02x}{g:02x}{b:02x}"

    # ---- Turbidity heuristic ----
    # Use grayscale contrast as a proxy for turbidity:
    #   - High stddev = high contrast = clearer water => lower turbidity_index
    #   - Low stddev  = flat image   = murkier water => higher turbidity_index
    gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
    std_intensity = float(gray.std())

    # Normalize std deviation to ~[0, 1] using a typical contrast scale.
    normalized_std = std_intensity / 64.0
    normalized_std = max(0.0, min(normalized_std, 1.0))

    turbidity_index = 1.0 - normalized_std

    return {
        "avg_color_hex": avg_color_hex,
        "turbidity_index": turbidity_index,
    }


def capture_snapshot() -> Path:
    """
    Capture a frame and save it as PNG in SNAPSHOT_DIR.

    Returns:
        Path to the written PNG file.
    """
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = SNAPSHOT_DIR / f"snapshot_{timestamp}.png"

    frame_rgb = _capture_raw_frame()

    # By default the images captured have the blue and red channels swapped
    # when written directly with OpenCV (which expects BGR), so we need to
    # swap them back around before calling cv2.imwrite.
    bgr_frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

    if not cv2.imwrite(str(file_path), bgr_frame):
        raise RuntimeError(f"Failed to write snapshot to {file_path}")

    return file_path


if __name__ == "__main__":
    metrics = compute_camera_metrics()
    path = capture_snapshot()
    print(f"Snapshot saved to {path}")
    print(f"Camera metrics: {metrics}")
