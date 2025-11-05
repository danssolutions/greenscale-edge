# greenscale-edge

## quick setup instructions

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y network-manager python3-pip python3-picamera2 libcamera-apps python3-opencv python3-flask python3-paho-mqtt
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
