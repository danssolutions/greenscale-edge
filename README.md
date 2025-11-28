# greenscale-edge

## Quick Setup Instructions

First, enable the required Raspberry Pi interfaces:

```bash
sudo raspi-config
```

Enable:

* **I2C** (`Interface Options → I2C → Enable`)
* **1-Wire** (`Interface Options → 1-Wire → Enable`)

Then reboot the device if it doesn't do so automatically:

```bash
sudo reboot
```

After reboot, install system dependencies:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    build-essential python3-dev python3-smbus git \
    network-manager python3-pip python3-picamera2 libcamera-apps \
    python3-opencv python3-flask python3-paho-mqtt
```

Load the 1-Wire kernel modules (these are usually auto-loaded):

```bash
sudo modprobe w1-gpio
sudo modprobe w1-therm
```

Finally, install and enable the systemd services:

```bash
sudo cp ~/greenscale-edge/systemd/greenscale-auto-ap.service /etc/systemd/system/
sudo cp ~/greenscale-edge/systemd/greenscale-edge-main.service /etc/systemd/system/
sudo cp ~/greenscale-edge/systemd/greenscale-edge-config.service /etc/systemd/system/
sudo cp ~/greenscale-edge/systemd/greenscale-pump.service /etc/systemd/system/

sudo systemctl daemon-reload

sudo systemctl enable --now greenscale-edge-main.service
```

If your repository is located somewhere other than `/home/user/greenscale-edge`,
update the `ExecStart` path in:

```
/etc/systemd/system/greenscale-edge-main.service
```

---

## Configuration

The edge agent reads its configuration from:

```
greenscale-edge/config.json
```

Supported fields include:

* `broker_host` (string): MQTT broker hostname or IP.
* `broker_port` (number): MQTT broker port (default `1883`).
* `broker_username` / `broker_password` (strings or `null`): authentication credentials.
* `publish_interval` (number): seconds between telemetry publishes.
* `tls_enable` (boolean): enable TLS when connecting to the broker.
* `tls_ca_cert` (string or `null`): path to CA certificate.
* `tls_client_cert` / `tls_client_key` (strings or `null`): paths for mutual TLS client auth.
* `tls_insecure` (boolean): skip certificate verification (not recommended except for testing).

Example secure configuration:

```json
{
  "broker_host": "mqtt.example.com",
  "broker_port": 8883,
  "publish_interval": 10,
  "broker_username": "edge-user",
  "broker_password": "super-secret",
  "tls_enable": true,
  "tls_ca_cert": "/etc/ssl/certs/ca-bundle.crt",
  "tls_client_cert": "/etc/ssl/certs/edge-device.pem",
  "tls_client_key": "/etc/ssl/private/edge-device.key",
  "tls_insecure": false
}
```