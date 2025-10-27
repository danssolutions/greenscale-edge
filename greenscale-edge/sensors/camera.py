#!/usr/bin/env python3

# [Dan] this is from a different project of mine that streams video using a camera module v2 over a flask web server
# this works with a v3 module also but has different goals from the project. TODO update this

import time

import cv2
from flask import Flask, Response
from picamera2 import Picamera2


app = Flask(__name__)
picam2 = Picamera2()

picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.start()


def generate_frames():
    while True:
        frame = picam2.capture_array()
        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )
        time.sleep(0.033)  # ~30 FPS cap


@app.route("/")
def index():
    return """
    <html>
      <head>
        <title>Camera Stream</title>
        <style>
          body, html {
            margin: 0;
            padding: 0;
            height: 100%;
            width: 100%;
            background: #000;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            background: #000;
          }
        </style>
      </head>
      <body>
        <img src="/stream.mjpg">
      </body>
    </html>
    """


@app.route("/stream.mjpg")
def stream():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
