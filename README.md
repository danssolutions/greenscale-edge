# greenscale-edge

## quick setup instructions

Enable I2C interface and 1-Wire interface through `sudo raspi-config`. Then reboot with `sudo reboot`.

Afterwards:
```bash
sudo apt update && sudo apt upgrade -y
sudo modprobe w1-gpio
sudo modprobe w1-therm
sudo apt install -y build-essential python3-dev python3-smbus i2c-tools git network-manager python3-pip python3-picamera2 libcamera-apps python3-opencv python3-flask python3-paho-mqtt
git clone https://github.com/DFRobot/DFRobot_ADS1115.git
cd ~/DFRobot_ADS1115/python/raspberrypi
sudo python DFRobot_ADS1115.py
sudo cp ~/greenscale-edge/systemd/greenscale-auto-ap.service /etc/systemd/system/
sudo cp ~/greenscale-edge/systemd/greenscale-edge-main.service /etc/systemd/system/
sudo cp ~/greenscale-edge/systemd/greenscale-edge-config.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable greenscale-edge-main.service
sudo systemctl start greenscale-edge-main.service
sudo systemctl enable greenscale-edge-config.service
sudo systemctl start greenscale-edge-config.service
```

Update the `ExecStart` path in `/etc/systemd/system/greenscale-edge-main.service`
if your repository lives somewhere other than `/home/user/greenscale-edge`.

## Configuration

The edge agent reads its settings from `greenscale-edge/config.json`. Supported
fields include:

- `broker_host` (string): MQTT broker hostname or IP.
- `broker_port` (number): MQTT broker port (default `1883`).
- `broker_username` / `broker_password` (strings or `null`): credentials for
  authenticated brokers.
- `publish_interval` (number): seconds between telemetry publishes.
- `tls_enable` (boolean): enable TLS when connecting to the broker (default
  `false`).
- `tls_ca_cert` (string or `null`): path to the CA certificate for broker
  validation.
- `tls_client_cert` / `tls_client_key` (strings or `null`): client certificate
  and key paths for mutual TLS.
- `tls_insecure` (boolean): allow insecure TLS (skips certificate verification);
  default is `false` and should remain disabled unless required for testing.

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