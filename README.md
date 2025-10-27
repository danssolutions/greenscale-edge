# greenscale-edge

## quick setup instructions

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y network-manager python3-pip python3-picamera2 libcamera-apps python3-opencv python3-flask
sudo cp ~/greenscale-edge/systemd/greenscale-auto-ap.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable greenscale-auto-ap.service
sudo systemctl start greenscale-auto-ap.service
```
Update the `ExecStart` path in `/etc/systemd/system/greenscale-auto-ap.service`
if your repository lives somewhere other than `/home/user/greenscale-edge`.
