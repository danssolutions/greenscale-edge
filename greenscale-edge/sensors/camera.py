#!/usr/bin/env python3

"""Capture a single snapshot from the camera and save it to disk.

Running this module directly will capture a single frame from the camera at the
Pi Camera Module 3's full still resolution (4608x2592) and save it as a PNG
image inside the ``snapshots`` directory at the project root.
"""

from __future__ import annotations

import datetime
from pathlib import Path
import time

import cv2
from picamera2 import Picamera2


SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "snapshots"


def capture_snapshot() -> Path:
    """Capture a frame and write it to the snapshots directory."""

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = SNAPSHOT_DIR / f"snapshot_{timestamp}.png"

    picam2 = Picamera2()
    configuration = picam2.create_still_configuration(
        main={"size": (4608, 2592)}
    )
    picam2.configure(configuration)
    picam2.start()

    # Give the sensor a short amount of time to collect exposure data
    time.sleep(0.5)
    frame = picam2.capture_array()
    picam2.stop()

    if frame is None:
        raise RuntimeError("Failed to capture image from camera")

    # By default the images captured have the blue and red channels swapped,
    # so we need to swap them back around before calling cv2.imwrite
    bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    if not cv2.imwrite(str(file_path), bgr_frame):
        raise RuntimeError(f"Failed to write snapshot to {file_path}")

    return file_path


if __name__ == "__main__":
    path = capture_snapshot()
    print(f"Snapshot saved to {path}")
