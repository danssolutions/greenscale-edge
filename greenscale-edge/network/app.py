#!/usr/bin/env python3
from pathlib import Path

from flask import Flask, request, render_template, redirect
import subprocess


def _run_nmcli(args):
    """Run an nmcli command and return the completed process."""
    return subprocess.run(
        ["nmcli", *args],
        check=False,
        capture_output=True,
        text=True,
    )


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
)


@app.route("/", methods=["GET", "POST"])
def wifi_setup():
    form_data = {
        "ssid": "",
        "auth_type": "psk",
        "password": "",
        "identity": "",
        "eap_password": "",
        "ca_cert": "",
    }
    error = None

    if request.method == "POST":
        form_data.update({
            "ssid": request.form.get("ssid", "").strip(),
            "auth_type": request.form.get("auth_type", "psk"),
            "password": request.form.get("password", ""),
            "identity": request.form.get("identity", "").strip(),
            "eap_password": request.form.get("eap_password", ""),
            "ca_cert": request.form.get("ca_cert", ""),
        })

        ssid = form_data["ssid"]
        auth_type = (form_data["auth_type"] or "psk").lower()

        if not ssid:
            error = "SSID is required."
        elif auth_type == "psk":
            password = form_data["password"].strip()
            if not password:
                error = "Password is required for WPA-PSK."
            else:
                result = _run_nmcli([
                    "device",
                    "wifi",
                    "connect",
                    ssid,
                    "password",
                    password,
                ])
                if result.returncode == 0:
                    return redirect("/success")
                error = (
                    result.stderr.strip()
                    or result.stdout.strip()
                    or "Failed to connect using WPA-PSK."
                )
        elif auth_type == "eap":
            identity = form_data["identity"]
            eap_password = form_data["eap_password"].strip()
            ca_cert_content = form_data["ca_cert"].strip()

            if not identity:
                error = "Identity / username is required for WPA-EAP."
            elif not eap_password:
                error = "Password is required for WPA-EAP."
            else:
                connection_name = ssid
                existing = _run_nmcli(["connection", "show", connection_name])
                if existing.returncode != 0:
                    created = _run_nmcli([
                        "connection",
                        "add",
                        "type",
                        "wifi",
                        "con-name",
                        connection_name,
                        "ifname",
                        "*",
                        "ssid",
                        ssid,
                    ])
                    if created.returncode != 0:
                        error = (
                            created.stderr.strip()
                            or created.stdout.strip()
                            or "Failed to create WPA-EAP profile."
                        )
                if error is None:
                    ca_cert_path = None
                    if ca_cert_content:
                        cert_dir = BASE_DIR / "certs"
                        cert_dir.mkdir(parents=True, exist_ok=True)
                        cert_path = cert_dir / f"{ssid}.pem"
                        if not ca_cert_content.endswith("\n"):
                            ca_cert_content += "\n"
                        cert_path.write_text(ca_cert_content)
                        ca_cert_path = str(cert_path)

                    commands = [
                        [
                            "connection",
                            "modify",
                            connection_name,
                            "802-11-wireless-security.key-mgmt",
                            "wpa-eap",
                        ],
                        [
                            "connection",
                            "modify",
                            connection_name,
                            "802-1x.eap",
                            "peap",
                        ],
                        [
                            "connection",
                            "modify",
                            connection_name,
                            "802-1x.phase2-auth",
                            "mschapv2",
                        ],
                        [
                            "connection",
                            "modify",
                            connection_name,
                            "802-1x.identity",
                            identity,
                        ],
                        [
                            "connection",
                            "modify",
                            connection_name,
                            "802-1x.password",
                            eap_password,
                        ],
                    ]

                    if ca_cert_path:
                        commands.append([
                            "connection",
                            "modify",
                            connection_name,
                            "802-1x.ca-cert",
                            ca_cert_path,
                        ])
                    else:
                        commands.append([
                            "connection",
                            "modify",
                            connection_name,
                            "802-1x.ca-cert",
                            "",
                        ])

                    for command in commands:
                        result = _run_nmcli(command)
                        if result.returncode != 0:
                            error = (
                                result.stderr.strip()
                                or result.stdout.strip()
                                or "Failed to configure WPA-EAP profile."
                            )
                            break

                if error is None:
                    bring_up = _run_nmcli([
                        "connection",
                        "up",
                        connection_name,
                    ])
                    if bring_up.returncode == 0:
                        return redirect("/success")
                    error = (
                        bring_up.stderr.strip()
                        or bring_up.stdout.strip()
                        or "Failed to activate WPA-EAP connection."
                    )
        else:
            error = "Unsupported authentication type."

    if error:
        form_data["password"] = ""
        form_data["eap_password"] = ""

    return render_template("wifi_setup.html", error=error, form_data=form_data)


@app.route("/success")
def success():
    import socket
    import subprocess
    hostname = socket.gethostname()
    res = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
    ips = res.stdout.strip().split()
    return render_template("wifi_success.html", hostname=hostname, ips=ips)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
