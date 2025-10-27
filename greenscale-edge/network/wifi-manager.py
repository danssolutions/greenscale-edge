#!/usr/bin/env python3
import os
import time
import socket
import subprocess
import uuid
import sys
from pathlib import Path

# Configuration via environment vars
INTERFACE = os.getenv("WIFI_IFACE", "wlan0")
WAIT_TIME = int(os.getenv("WIFI_WAIT_SEC", "30"))
AP_BASE_SSID = os.getenv("AP_BASE_SSID", "Greenscale")


def get_device_id():
    try:
        mac = uuid.getnode()
        return f"{mac & 0xFFFF:04X}"
    except Exception as e:
        return str(uuid.uuid4())[:4]


def wifi_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), 2)
        return True
    except OSError:
        return False


def get_ap_ip():
    try:
        result = subprocess.run(
            ["ip", "addr", "show", INTERFACE],
            capture_output=True, text=True, check=False
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                ip_cidr = line.split()[1]
                ip = ip_cidr.split("/")[0]
                return ip
        return None
    except Exception as e:
        return None


def start_access_point():
    dev_id = get_device_id()
    ssid = f"{AP_BASE_SSID}-{dev_id}"

    # Delete existing connection with this SSID (if any)
    subprocess.run(["nmcli", "connection", "delete", ssid], check=False)

    # Create new open AP connection
    subprocess.run([
        "nmcli", "connection", "add",
        "type", "wifi",
        "ifname", INTERFACE,
        "con-name", ssid,
        "autoconnect", "yes",
        "ssid", ssid,
        "802-11-wireless.mode", "ap",
        "802-11-wireless.band", "bg",
        "ipv4.method", "shared",
        "ipv6.method", "ignore"
    ], check=False)

    # Bring it up
    subprocess.run(["nmcli", "connection", "up", ssid], check=False)

    time.sleep(3)  # give interface time to settle
    ap_ip = get_ap_ip()

    # Launch config portal UI
    script_dir = Path(__file__).resolve().parent
    script_path = script_dir / "app.py"
    if script_path.exists():
        proc = subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=str(script_dir),
        )

    # Keep this script alive so service doesn’t exit
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass


def main():
    waited = 0
    while waited < WAIT_TIME:
        if wifi_connected():
            return
        time.sleep(1)
        waited += 1

    start_access_point()


if __name__ == "__main__":
    main()
