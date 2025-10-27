#!/usr/bin/env python3
import logging
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


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def get_device_id():
    try:
        mac = uuid.getnode()
        return f"{mac & 0xFFFF:04X}"
    except Exception:
        return str(uuid.uuid4())[:4]


def wifi_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), 2)
        return True
    except OSError:
        return False


def list_saved_wifi_connections():
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        logger.error("nmcli not found; cannot query saved Wi-Fi profiles")
        return []

    if result.returncode != 0:
        logger.warning(
            "Failed to list saved connections (rc=%s): %s",
            result.returncode,
            result.stderr.strip(),
        )
        return []

    wifi_connections = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        parts = line.split(":")
        if len(parts) < 2:
            continue
        name = parts[0]
        conn_type = parts[1]
        if conn_type in {"wifi", "802-11-wireless"}:
            wifi_connections.append(name)

    return wifi_connections


def get_connection_state(name):
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "GENERAL.STATE", "connection", "show", name],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None

    if result.returncode != 0:
        return None

    state_line = result.stdout.strip()
    if not state_line:
        return None

    # Expected format: GENERAL.STATE:activated (or similar)
    if ":" in state_line:
        _, value = state_line.split(":", 1)
    else:
        value = state_line
    return value.strip()


def activate_wifi_connection(name):
    logger.info("Attempting to activate Wi-Fi profile '%s'", name)

    try:
        result = subprocess.run(
            ["nmcli", "connection", "up", name],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        logger.error(
            "nmcli not found; cannot activate Wi-Fi profile '%s'",
            name,
        )
        return False

    if result.returncode != 0:
        logger.warning(
            "Activation of '%s' failed (rc=%s): %s",
            name,
            result.returncode,
            result.stderr.strip() or result.stdout.strip(),
        )
    else:
        logger.info("nmcli accepted activation command for '%s'", name)

    wait_seconds = max(0, WAIT_TIME)
    for _ in range(wait_seconds):
        if wifi_connected():
            logger.info(
                "Wi-Fi connection established after activating '%s'",
                name,
            )
            return True
        time.sleep(1)

    state = get_connection_state(name)
    if state:
        logger.info(
            "Connection '%s' state after activation attempt: %s",
            name,
            state,
        )
    else:
        logger.info("Unable to determine connection state for '%s'", name)

    return wifi_connected()


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
    except Exception:
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
    if ap_ip:
        logger.info("Access point started on %s with SSID '%s'", ap_ip, ssid)
    else:
        logger.info("Access point started with SSID '%s'", ssid)

    # Launch config portal UI
    script_dir = Path(__file__).resolve().parent
    script_path = script_dir / "app.py"
    if script_path.exists():
        logger.info("Launching configuration portal UI from %s", script_path)
        subprocess.Popen(
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
    if wifi_connected():
        logger.info("Wi-Fi already connected; skipping AP setup")
        return

    wifi_profiles = list_saved_wifi_connections()
    if not wifi_profiles:
        logger.info("No saved Wi-Fi profiles found")
    else:
        logger.info("Found %d saved Wi-Fi profiles", len(wifi_profiles))
        logger.info("Attempt order: %s", ", ".join(wifi_profiles))

    for profile in wifi_profiles:
        if activate_wifi_connection(profile):
            logger.info("Connected to Wi-Fi using profile '%s'", profile)
            return

    if wifi_connected():
        logger.info("Wi-Fi connection succeeded without AP")
        return

    logger.warning(
        "Failed to establish Wi-Fi connection; starting access point"
    )
    start_access_point()


if __name__ == "__main__":
    main()
