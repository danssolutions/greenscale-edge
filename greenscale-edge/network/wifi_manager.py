#!/usr/bin/env python3
"""
Greenscale Wi-Fi Manager
------------------------
- Connects to known Wi-Fi profiles on boot.
- Starts access point + setup portal if none are available.
"""

import logging
import os
import time
import subprocess
import sys
import hashlib
from pathlib import Path

# --- Configuration ---
INTERFACE = os.getenv("WIFI_IFACE", "wlan0")
WAIT_TIME = int(os.getenv("WIFI_WAIT_SEC", "20"))
AP_BASE_SSID = os.getenv("AP_BASE_SSID", "Greenscale")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("wifi_manager")

# --- Helpers ---------------------------------------------------------------


def get_device_id() -> str:
    """Generate stable 4-char device suffix from /etc/machine-id."""
    try:
        mid = Path("/etc/machine-id").read_text().strip()
        return hashlib.sha1(mid.encode()).hexdigest()[:4].upper()
    except Exception:
        return "0000"


def wifi_connected() -> bool:
    """Return True if wlan0 is connected to any network."""
    try:
        res = subprocess.run(
            ["nmcli", "-t", "-f", "DEVICE,STATE", "device"],
            capture_output=True, text=True, check=False
        )
        return any(f"{INTERFACE}:connected" in line for line in res.stdout.splitlines())
    except Exception as e:
        log.warning("Wi-Fi check failed: %s", e)
        return False


def list_wifi_profiles():
    """List saved Wi-Fi profiles."""
    try:
        res = subprocess.run(
            ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
            capture_output=True, text=True
        )
        return [line.split(":")[0] for line in res.stdout.splitlines() if ":wifi" in line]
    except Exception as e:
        log.error("Unable to list Wi-Fi profiles: %s", e)
        return []


def activate_profile(name: str) -> bool:
    """Try to bring up a known Wi-Fi connection."""
    log.info("Activating Wi-Fi profile '%s'...", name)
    subprocess.run(["nmcli", "connection", "up", name], check=False)
    for _ in range(WAIT_TIME):
        if wifi_connected():
            log.info("Connected using profile '%s'", name)
            return True
        time.sleep(1)
    log.warning("Failed to connect using '%s'", name)
    return False

# --- Access Point ----------------------------------------------------------


def start_access_point():
    """Create and start the fallback access point + config portal."""
    dev_id = get_device_id()
    ssid = f"{AP_BASE_SSID}-{dev_id}"

    # Delete any old connection with same SSID
    subprocess.run(["nmcli", "connection", "delete", ssid], check=False)

    log.info("Starting access point '%s'...", ssid)
    subprocess.run([
        "nmcli", "connection", "add",
        "type", "wifi", "ifname", INTERFACE,
        "con-name", ssid,
        "autoconnect", "yes",
        "ssid", ssid,
        "802-11-wireless.mode", "ap",
        "802-11-wireless.band", "bg",
        "ipv4.method", "shared",
        "ipv6.method", "ignore"
    ], check=False)

    subprocess.run(["nmcli", "connection", "up", ssid], check=False)
    time.sleep(3)

    log.info("Access point '%s' active. Launching config portal...", ssid)
    portal = Path(__file__).resolve().parent / "app.py"
    if portal.exists():
        subprocess.Popen([sys.executable, str(portal)], cwd=str(portal.parent))
    else:
        log.warning("Portal app.py not found!")

    # Keep alive indefinitely
    while True:
        time.sleep(60)

# --- Main ------------------------------------------------------------------


def main():
    # if already connected, done
    if wifi_connected():
        log.info("Wi-Fi already connected.")
        return

    profiles = list_wifi_profiles()
    connected = False

    if profiles:
        log.info("Found saved profiles: %s", ", ".join(profiles))
        for p in profiles:
            if activate_profile(p):
                connected = True
                break
    else:
        log.info("No saved profiles found.")

    # If connection succeeded, stop here
    if connected and wifi_connected():
        log.info("Wi-Fi connection established.")
        return

    # 🔻 Always fall back here if nothing worked
    log.warning("No active Wi-Fi. Starting fallback access point...")
    start_access_point()

# ---------------------------------------------------------------------------


if __name__ == "__main__":
    main()
