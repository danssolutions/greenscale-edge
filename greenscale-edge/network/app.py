#!/usr/bin/env python3
from pathlib import Path

from flask import Flask, request, render_template, redirect
import subprocess


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
)


@app.route("/", methods=["GET", "POST"])
def wifi_setup():
    if request.method == "POST":
        ssid = request.form.get("ssid", "").strip()
        password = request.form.get("password", "").strip()
        if ssid and password:
            # Use nmcli to connect
            subprocess.run([
                "nmcli", "device", "wifi", "connect", ssid,
                "password", password
            ], check=False)
            return redirect("/success")
        else:
            return render_template(
                "wifi-setup.html",
                error="SSID and password required",
            )
    return render_template("wifi-setup.html", error=None)


@app.route("/success")
def success():
    return (
        "Configuration saved. Attempting to connect to network. "
        "You may now disconnect from the hotspot."
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
