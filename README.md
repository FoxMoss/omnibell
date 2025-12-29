# Omnibell
## A doorbell for everyone

Built with flask + websockets!

## How to install

Install Python 3.13.7 or above.

Install packages:
```
pip install flask flask_sock requests
```

### Running (Development)
```
flask --app main run
```

### Running (Production)
```
gunicorn main:app -b :5001 --threads 100
```

Or as a systemd service:
```
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
# gunicorn can let systemd know when it is ready
Type=notify
NotifyAccess=main
# the specific user that our service will run as
# this user can be transiently created by systemd
# DynamicUser=true
RuntimeDirectory=gunicorn
WorkingDirectory=/var/omnibell
ExecStart=/var/omnibell/.venv/bin/gunicorn main:app -b :5001 --threads 100
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
# if your app does not need administrative capabilities, let systemd know
# ProtectSystem=strict

[Install]
WantedBy=multi-user.target
```
