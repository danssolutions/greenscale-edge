# greenscale-edge

## quick setup instructions

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y network-manager python3-pip python3-picamera2 libcamera-apps python3-opencv python3-flask
sudo cp ~/greenscale-edge/systemd/wifi-manager.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wifi-manager.service
sudo systemctl start wifi-manager.service
```
