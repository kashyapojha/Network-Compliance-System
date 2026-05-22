"""
Network Device Naming Compliance Monitor
=========================================
Monitors devices joining the network and alerts admin
if hostname doesn't follow company naming conventions.

Author   : Intern Project
Version  : 1.0.0
"""

import re
import json
import smtplib
import logging
import sqlite3
import socket
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# ─── Resolve Paths dynamically ──────────────────────────────────────────────
MONITOR_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = MONITOR_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOGS_DIR / "monitor.log")),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


# ─── Config ─────────────────────────────────────────────────────────────────
CONFIG = {
    "admin_email"   : "admin@company.com",
    "smtp_host"     : "smtp.company.com",
    "smtp_port"     : 587,
    "smtp_user"     : "alerts@company.com",
    "smtp_password" : "your_password_here",

    # Naming policy
    "dept_prefixes" : ["IT", "HR", "FIN", "OPS", "DEV", "MKT"],
    "device_types"  : ["WS", "LPT", "SRV", "PRN", "MOB", "CAM", "IOT"],
    "pattern"       : r"^(IT|HR|FIN|OPS|DEV|MKT)-(WS|LPT|SRV|PRN|MOB|CAM|IOT)-\d{4}$",

    # DB path
    "db_path"       : str(LOGS_DIR / "devices.db"),
    "poll_interval" : 30,   # seconds
    "network_range" : "192.168.1.0/24",
}

DEPT_MAP = {
    "IT": "IT Operations", "HR": "Human Resources",
    "FIN": "Finance",      "OPS": "Operations",
    "DEV": "Development",  "MKT": "Marketing",
}


# ─── Database ────────────────────────────────────────────────────────────────
def init_db(db_path: str):
    """Create tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname    TEXT NOT NULL,
            ip_address  TEXT,
            mac_address TEXT,
            compliant   INTEGER DEFAULT 0,
            first_seen  TEXT,
            last_seen   TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname   TEXT NOT NULL,
            ip_address TEXT,
            reason     TEXT,
            sent_at    TEXT
        )
    """)
    conn.commit()
    conn.close()
    log.info("Database initialised at %s", db_path)


def save_device(hostname: str, ip: str, mac: str, compliant: bool):
    conn = sqlite3.connect(CONFIG["db_path"])
    now = datetime.datetime.now().isoformat()
    existing = conn.execute(
        "SELECT id FROM devices WHERE hostname = ?", (hostname,)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE devices SET last_seen=?, ip_address=?, compliant=? WHERE hostname=?",
            (now, ip, int(compliant), hostname)
        )
    else:
        conn.execute(
            "INSERT INTO devices (hostname,ip_address,mac_address,compliant,first_seen,last_seen)"
            " VALUES (?,?,?,?,?,?)",
            (hostname, ip, mac, int(compliant), now, now)
        )
    conn.commit()
    conn.close()


def save_alert(hostname: str, ip: str, reason: str):
    conn = sqlite3.connect(CONFIG["db_path"])
    conn.execute(
        "INSERT INTO alerts (hostname, ip_address, reason, sent_at) VALUES (?,?,?,?)",
        (hostname, ip, reason, datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_all_devices():
    conn = sqlite3.connect(CONFIG["db_path"])
    rows = conn.execute(
        "SELECT hostname, ip_address, mac_address, compliant, first_seen FROM devices ORDER BY first_seen DESC"
    ).fetchall()
    conn.close()
    return rows


def get_all_alerts():
    conn = sqlite3.connect(CONFIG["db_path"])
    rows = conn.execute(
        "SELECT hostname, ip_address, reason, sent_at FROM alerts ORDER BY sent_at DESC"
    ).fetchall()
    conn.close()
    return rows


# ─── Naming Policy ───────────────────────────────────────────────────────────
def check_compliance(hostname: str) -> tuple[bool, list[str]]:
    """
    Returns (is_compliant, list_of_failures).
    Rules:
      1. Starts with valid dept prefix
      2. Contains valid device-type segment
      3. Ends with 4-digit number
      4. All uppercase
      5. Length 10–20 chars
    """
    failures = []
    name = hostname.strip().upper()

    dept_ok = any(name.startswith(p + "-") for p in CONFIG["dept_prefixes"])
    if not dept_ok:
        failures.append(f"Must start with a dept prefix ({', '.join(CONFIG['dept_prefixes'])})")

    type_ok = any(f"-{t}-" in name for t in CONFIG["device_types"])
    if not type_ok:
        failures.append(f"Must contain a device type ({', '.join(CONFIG['device_types'])})")

    if not name[-4:].isdigit() or name[-5] != "-":
        failures.append("Must end with -XXXX (4-digit ID)")

    if hostname != hostname.upper():
        failures.append("Hostname must be fully uppercase")

    if not (10 <= len(hostname) <= 20):
        failures.append("Length must be between 10 and 20 characters")

    compliant = len(failures) == 0
    return compliant, failures


# ─── Email Alert ─────────────────────────────────────────────────────────────
def send_alert_email(hostname: str, ip: str, mac: str, failures: list[str]):
    """Send an HTML alert email to the admin."""
    subject = f"[ALERT] Non-compliant device detected: {hostname}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    failure_rows = "".join(
        f"<tr><td style='padding:6px 12px;color:#c0392b'>✗ {f}</td></tr>"
        for f in failures
    )

    html_body = f"""
    <html><body style='font-family:Arial,sans-serif;color:#333'>
      <h2 style='color:#c0392b'>⚠ Network Naming Violation Detected</h2>
      <table style='border-collapse:collapse;width:100%;max-width:500px'>
        <tr style='background:#f5f5f5'><td style='padding:6px 12px'><b>Hostname</b></td><td style='padding:6px 12px'>{hostname}</td></tr>
        <tr><td style='padding:6px 12px'><b>IP Address</b></td><td style='padding:6px 12px'>{ip}</td></tr>
        <tr style='background:#f5f5f5'><td style='padding:6px 12px'><b>MAC Address</b></td><td style='padding:6px 12px'>{mac}</td></tr>
        <tr><td style='padding:6px 12px'><b>Detected at</b></td><td style='padding:6px 12px'>{now_str}</td></tr>
      </table>
      <h3 style='margin-top:20px'>Policy violations:</h3>
      <table style='border-collapse:collapse'>{failure_rows}</table>
      <p style='margin-top:20px;font-size:13px;color:#888'>
        This alert was generated automatically by the Network Naming Compliance Monitor.
      </p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = CONFIG["smtp_user"]
    msg["To"]      = CONFIG["admin_email"]
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(CONFIG["smtp_host"], CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(CONFIG["smtp_user"], CONFIG["smtp_password"])
            server.sendmail(CONFIG["smtp_user"], CONFIG["admin_email"], msg.as_string())
        log.info("Alert email sent to %s for device %s", CONFIG["admin_email"], hostname)
    except Exception as exc:
        log.error("Failed to send alert email: %s", exc)


# ─── Webhook Alert (Slack / Teams) ───────────────────────────────────────────
def send_webhook_alert(hostname: str, ip: str, failures: list[str], webhook_url: str):
    """POST a JSON alert to a Slack/Teams webhook URL."""
    import urllib.request
    payload = {
        "text": f"*⚠ Non-compliant device*: `{hostname}` ({ip})\n"
                + "\n".join(f"• {f}" for f in failures)
    }
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(webhook_url, data=data,
                                   headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=5)
        log.info("Webhook alert sent for %s", hostname)
    except Exception as exc:
        log.error("Webhook failed: %s", exc)


# ─── Network Scanner (ARP / Socket ping) ─────────────────────────────────────
def scan_network_arp(network_range: str) -> list[dict]:
    """
    Uses scapy (if available) for ARP scan, otherwise falls back to
    socket-based hostname resolution.
    Returns list of {hostname, ip, mac}.
    """
    try:
        from scapy.all import ARP, Ether, srp
        log.info("Scanning network with ARP: %s", network_range)
        arp  = ARP(pdst=network_range)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        result, _ = srp(ether / arp, timeout=3, verbose=False)
        devices = []
        for _, rcv in result:
            ip  = rcv.psrc
            mac = rcv.hwsrc
            try:
                hostname = socket.gethostbyaddr(ip)[0].split(".")[0].upper()
            except socket.herror:
                hostname = ip.replace(".", "-")
            devices.append({"hostname": hostname, "ip": ip, "mac": mac})
        return devices
    except ImportError:
        log.warning("scapy not installed — using demo mode")
        return _demo_devices()


def _demo_devices() -> list[dict]:
    """Return sample devices for testing without real network access."""
    import random
    pool = [
        ("IT-WS-0042",   "192.168.1.10"),
        ("HR-LPT-0023",  "192.168.1.11"),
        ("DEV-SRV-0099", "192.168.1.12"),
        ("johns-laptop",  "192.168.1.50"),
        ("WORKSTATION42", "192.168.1.51"),
        ("OPS-CAM-0012",  "192.168.1.13"),
        ("fin-ws-99",     "192.168.1.52"),
        ("MKT-MOB-0301",  "192.168.1.14"),
    ]
    seen = random.sample(pool, k=random.randint(3, 6))
    return [
        {"hostname": h, "ip": ip,
         "mac": ":".join(f"{random.randint(0,255):02X}" for _ in range(6))}
        for h, ip in seen
    ]


# ─── Main Loop ───────────────────────────────────────────────────────────────
def run_monitor():
    """Main monitoring loop."""
    import time
    init_db(CONFIG["db_path"])
    log.info("Network Naming Compliance Monitor started")
    log.info("Policy pattern: %s", CONFIG["pattern"])

    known_violations = set()   # avoid duplicate alerts

    while True:
        devices = scan_network_arp(CONFIG["network_range"])
        for dev in devices:
            hostname = dev["hostname"]
            ip       = dev["ip"]
            mac      = dev["mac"]

            compliant, failures = check_compliance(hostname)
            save_device(hostname, ip, mac, compliant)

            if compliant:
                log.info("[OK]      %s (%s)", hostname, ip)
            else:
                log.warning("[VIOLATION] %s (%s) — %s", hostname, ip, "; ".join(failures))
                if hostname not in known_violations:
                    known_violations.add(hostname)
                    send_alert_email(hostname, ip, mac, failures)
                    save_alert(hostname, ip, "; ".join(failures))

        log.info("Scan complete. Next scan in %ds.", CONFIG["poll_interval"])
        time.sleep(CONFIG["poll_interval"])


if __name__ == "__main__":
    run_monitor()
