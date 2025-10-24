#!/usr/bin/env python3
import os
import time
import socket
import subprocess
import uuid
import logging
import sys
from pathlib import Path

# Setup logging
LOG_FILE = "/var/log/greenscale-wifi-manager.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE)
    ]
)

# Configuration via environment vars
INTERFACE    = os.getenv("WIFI_IFACE", "wlan0")
WAIT_TIME    = int(os.getenv("WIFI_WAIT_SEC", "30"))
AP_BASE_SSID = os.getenv("AP_BASE_SSID", "Greenscale")

def get_device_id():
    try:
        mac = uuid.getnode()
        return f"{mac & 0xFFFF:04X}"
    except Exception as e:
        logging.warning(f"Could not get MAC device id: {e}")
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
        logging.error(f"Error getting IP for {INTERFACE}: {e}")
        return None

def start_access_point():
    dev_id = get_device_id()
    ssid   = f"{AP_BASE_SSID}-{dev_id}"
    logging.info(f"Enabling Access Point mode on {INTERFACE}, SSID={ssid} (open network)")

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
    if ap_ip:
        logging.info(f"AP mode active. Connect to SSID '{ssid}' and browse to http://{ap_ip}/")
    else:
        logging.warning("AP mode active but could not determine gateway IP!")

    # Launch config portal UI
    script_path = Path(__file__).parent / "web_config" / "app.py"
    if script_path.exists():
        logging.info("Starting configuration portal UI …")
        proc = subprocess.Popen(["python3", str(script_path)])
        logging.info(f"Config portal process started (PID={proc.pid})")
    else:
        logging.warning(f"Config UI script not found at {script_path}")

    # Keep this script alive so service doesn’t exit
    logging.info("Entering keep-alive loop so UI stays available.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("Keep-alive loop interrupted, exiting.")

def main():
    logging.info("Starting WiFi Manager — checking connectivity.")
    waited = 0
    while waited < WAIT_TIME:
        if wifi_connected():
            logging.info("WiFi detected — normal mode.")
            return
        time.sleep(1)
        waited += 1

    logging.info(f"No WiFi within {WAIT_TIME} seconds — falling back to AP mode.")
    start_access_point()

if __name__ == "__main__":
    main()
