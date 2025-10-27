#!/usr/bin/env python3
from flask import Flask, request, render_template, redirect
import subprocess

app = Flask(__name__, template_folder="templates")


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
            return render_template("wifi_setup.html", error="SSID and password required")
    return render_template("wifi_setup.html", error=None)


@app.route("/success")
def success():
    return "Configuration saved. Attempting to connect to network. You may now disconnect from the hotspot."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
