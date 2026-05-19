# Network Device Naming Compliance Monitor

## Overview
Monitors devices joining the network and instantly alerts the admin
if the device hostname violates the company naming convention.

## Naming Policy
Format: `DEPT-TYPE-NNNN`
- Dept prefix  : IT, HR, FIN, OPS, DEV, MKT
- Device type  : WS, LPT, SRV, PRN, MOB, CAM, IOT
- Numeric ID   : 4 digits (e.g. 0042)
- All uppercase, 10–20 characters

Valid examples  : IT-WS-0042 | DEV-SRV-0099 | HR-LPT-0023
Invalid examples: johns-laptop | WORKSTATION42 | fin-ws-99

## Quick Start
```bash
pip install -r requirements.txt
python src/monitor.py          # CLI monitor (background daemon)
python src/dashboard.py        # Web dashboard → http://localhost:5000
python tests/test_compliance.py  # Run unit tests
```

## Project Structure
```
network-monitor/
├── src/
│   ├── monitor.py      ← Core engine (scanning, compliance, alerts)
│   └── dashboard.py    ← Flask web dashboard
├── tests/
│   └── test_compliance.py
├── logs/               ← Auto-created (monitor.log, devices.db)
├── requirements.txt
└── README.md
```

## Alert Channels
- Email (SMTP) — configure CONFIG in monitor.py
- Webhook (Slack/Teams) — call send_webhook_alert()

## Tech Stack
Python 3.10+, Flask, Scapy, SQLite3, smtplib
