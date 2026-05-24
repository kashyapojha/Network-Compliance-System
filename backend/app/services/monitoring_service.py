import threading
import time
import logging
import re
import ipaddress
import subprocess
import platform
from datetime import datetime
from sqlalchemy.orm import Session
import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..database import get_db
from ..models.device import Device
from ..models.alert import Alert, AlertSeverity, AlertType
from ..services.fingerprinting_service import FingerprintingService
from ..utils.network_utils import get_network_cidr, normalize_mac
from ..config import Config
import os
import json

log = logging.getLogger(__name__)

# Set from app factory for real-time WebSocket alerts
_socketio = None


def set_monitoring_socketio(socketio_instance):
    global _socketio
    _socketio = socketio_instance


class MonitoringService:
    """Network monitoring service for compliance checking."""

    POLICY_ALERT_TYPES = (
        AlertType.UNKNOWN_DEVICE,
        AlertType.NAMING_VIOLATION,
        AlertType.SUSPICIOUS_ACTIVITY,
        AlertType.HOSTNAME_CHANGE,
    )

    def __init__(self, network_range=None, poll_interval=None):
        if not network_range or network_range == 'auto':
            network_range = None

        self.network_range = (
            network_range
            or (Config.NETWORK_RANGE if Config.NETWORK_RANGE and Config.NETWORK_RANGE != 'auto' else None)
            or get_network_cidr()
        )
        self.poll_interval = poll_interval or Config.POLL_INTERVAL
        self.is_running = False
        self.detected_devices = []
        self.alert_count = 0
        self.fingerprinting = FingerprintingService()
        self._thread = None

        self.naming_pattern = os.getenv(
            'NAMING_PATTERN',
            r'^[A-Z]{2,3}-[A-Z]{2,4}-\d{4}$'
        )
        self.naming_description = os.getenv(
            'NAMING_DESCRIPTION',
            'DEPT-DEVICETYPE-NNNN (e.g., IT-WS-0042, HR-LPT-0023)'
        )

        # Scan history log — written after every scan, read by /api/monitoring/scan-history
        self._scan_history_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '..', '..', 'monitoring', 'logs', 'scan_history.json'
        )

        self.smtp_enabled = os.getenv('SMTP_ENABLED', 'false').lower() == 'true'
        self.smtp_host = Config.SMTP_HOST or 'localhost'
        self.smtp_port = Config.SMTP_PORT
        self.smtp_user = Config.SMTP_USER
        self.smtp_password = Config.SMTP_PASSWORD
        self.admin_email = Config.ADMIN_EMAIL or 'admin@company.com'

    def start(self):
        """Start the continuous monitoring loop."""
        self.is_running = True
        log.info(f"Starting network monitoring on {self.network_range}")

        while self.is_running:
            try:
                self.scan_and_check()
                time.sleep(self.poll_interval)
            except Exception as e:
                log.error(f"Monitoring error: {e}")
                time.sleep(5)

    def stop(self):
        self.is_running = False
        log.info("Stopping network monitoring")

    def _is_ip_in_network_range(self, ip):
        """Check if IP address is within the configured network range."""
        try:
            ip_obj = ipaddress.ip_address(ip)
            network = ipaddress.ip_network(self.network_range, strict=False)
            return ip_obj in network
        except Exception:
            return False

    def scan_network(self):
        try:
            from scapy.all import ARP, Ether, srp
            log.info(f"Scanning network: {self.network_range}")
            arp = ARP(pdst=self.network_range)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            result, _ = srp(ether / arp, timeout=3, verbose=False)

            devices = []
            for _, rcv in result:
                ip = rcv.psrc
                mac = normalize_mac(rcv.hwsrc)

                if not self._is_ip_in_network_range(ip):
                    log.debug(f"Skipping device {ip} - not in network range {self.network_range}")
                    continue

                try:
                    hostname = socket.gethostbyaddr(ip)[0].split(".")[0].upper()
                except socket.herror:
                    hostname = f"UNKNOWN-{mac.replace(':', '-')}"

                fingerprint = self.fingerprinting.identify_device(mac, ip)
                devices.append({
                    'hostname': hostname,
                    'ip_address': ip,
                    'mac_address': mac,
                    'vendor': fingerprint.get('vendor', 'Unknown'),
                    'os': fingerprint.get('os', 'Unknown'),
                    'detected_at': datetime.utcnow().isoformat()
                })

            self.detected_devices = devices
            log.info(f"Detected {len(devices)} devices in network range")
            return devices

        except ImportError as e:
            log.error(f"Scapy not installed: {e}")
            return self._demo_devices()
        except PermissionError as e:
            log.error(f"Permission denied - need Administrator privileges: {e}")
            log.info("Falling back to Windows ARP scan method")
            return self._scan_windows_arp()
        except OSError as e:
            log.error(f"OS error during scan: {e}")
            log.info("Falling back to Windows ARP scan method")
            return self._scan_windows_arp()
        except Exception as e:
            log.error(f"Network scan failed: {e}")
            log.info("Falling back to Windows ARP scan method")
            return self._scan_windows_arp()

    def scan_and_check(self):
        devices = self.scan_network()
        alerts_before = self.alert_count
        db: Session = next(get_db())
        try:
            for dev in devices:
                self._check_device_compliance(db, dev)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        alerts_created = self.alert_count - alerts_before
        self._write_scan_history(len(devices), alerts_created)
        return devices

    def _write_scan_history(self, devices_found, alerts_created):
        """Append scan result to a rolling JSON log (max 20 entries)."""
        try:
            os.makedirs(os.path.dirname(self._scan_history_path), exist_ok=True)
            try:
                with open(self._scan_history_path, 'r') as f:
                    history = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                history = []

            history.insert(0, {
                'timestamp': datetime.utcnow().isoformat(),
                'network_range': self.network_range,
                'devices_found': devices_found,
                'alerts_created': alerts_created,
            })
            history = history[:20]  # keep last 20 scans

            with open(self._scan_history_path, 'w') as f:
                json.dump(history, f)
        except Exception as e:
            log.error(f"Failed to write scan history: {e}")

    def get_scan_history(self):
        """Read scan history log. Returns list newest-first."""
        try:
            with open(self._scan_history_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _find_registered_device(self, db, mac, hostname):
        """Match by MAC first, then registered hostname (case-insensitive)."""
        device = db.query(Device).filter(Device.mac_address == mac).first()
        if device:
            return device
        if hostname and not hostname.startswith('UNKNOWN'):
            return db.query(Device).filter(
                Device.hostname.ilike(hostname)
            ).first()
        return None

    def _check_device_compliance(self, db, device_data):
        mac = normalize_mac(device_data['mac_address'])
        ip = device_data['ip_address']
        hostname = (device_data['hostname'] or '').upper()

        existing = self._find_registered_device(db, mac, hostname)

        if not existing:
            self._alert_unregistered_device(db, device_data, mac, ip, hostname)
            return

        existing.last_seen = datetime.utcnow()
        existing.ip_address = ip
        existing.times_seen = (existing.times_seen or 0) + 1

        # FIX: Resolve stale alerts keyed to the old MAC before updating it,
        # so we don't leave orphaned unresolved alerts behind when the MAC changes.
        if mac and existing.mac_address != mac:
            self._resolve_alerts_by_mac(db, existing.mac_address, existing.id)
            existing.mac_address = mac

        if existing.is_authorized and not existing.is_quarantined:
            self._resolve_policy_alerts(db, existing)
            self._update_trust_score(existing)
            return

        self._alert_registered_unauthorized(db, existing, mac, ip, hostname)
        self._check_network_anomalies(db, existing, mac, ip, hostname)
        self._update_trust_score(existing)

    def _alert_unregistered_device(self, db, device_data, mac, ip, hostname):
        """Single combined alert for unknown / unregistered devices."""
        is_valid, naming_reason = self._validate_naming_convention(hostname)
        parts = [f"Device with MAC {mac} and IP {ip} is not registered."]
        if not is_valid:
            parts.append(naming_reason)
        description = ' '.join(parts)

        alert = self._create_alert(
            db,
            AlertType.UNKNOWN_DEVICE,
            AlertSeverity.HIGH,
            f"Unauthorized device detected: {hostname}",
            description,
            ip,
            mac,
        )
        if alert:
            self._send_email_alert(alert.title, alert.description, device_data)
            self._emit_realtime('alert', {
                'id': alert.id,
                'title': alert.title,
                'severity': alert.severity.value,
                'description': alert.description,
            })

    def _alert_registered_unauthorized(self, db, device, mac, ip, hostname):
        """One combined alert for registered but not authorized devices."""
        is_valid, naming_reason = self._validate_naming_convention(hostname)
        parts = [f"Device {device.hostname} is registered but not authorized."]
        if not is_valid:
            parts.append(naming_reason)

        alert = self._create_alert(
            db,
            AlertType.SUSPICIOUS_ACTIVITY,
            AlertSeverity.HIGH,
            f"Unauthorized device on network: {hostname}",
            ' '.join(parts),
            ip,
            mac,
            device_id=device.id,
        )

        # FIX: registered-but-unauthorized devices were silently skipped for
        # real-time notifications. Emit the socket event and send email here
        # the same way unregistered devices do, so admins are always notified.
        if alert:
            self._send_email_alert(alert.title, alert.description, {
                'hostname': hostname,
                'ip_address': ip,
                'mac_address': mac,
            })
            self._emit_realtime('alert', {
                'id': alert.id,
                'title': alert.title,
                'severity': alert.severity.value,
                'description': alert.description,
            })

    def _check_network_anomalies(self, db, device, mac, ip, hostname):
        """Security checks that apply even to unauthorized registered devices."""
        if device.hostname.upper() != hostname and not hostname.startswith('UNKNOWN'):
            self._create_alert(
                db,
                AlertType.HOSTNAME_CHANGE,
                AlertSeverity.MEDIUM,
                f"Hostname changed for device {device.hostname}",
                f"Device changed from {device.hostname} to {hostname}",
                ip,
                mac,
                device_id=device.id,
            )
            device.hostname = hostname

        other = db.query(Device).filter(
            Device.ip_address == ip,
            Device.mac_address != mac,
            Device.id != device.id,
        ).first()
        if other:
            self._create_alert(
                db,
                AlertType.MAC_SPOOFING,
                AlertSeverity.CRITICAL,
                "Potential MAC spoofing detected",
                f"IP {ip} now associated with MAC {mac} (was {other.hostname})",
                ip,
                mac,
            )

    def _resolve_policy_alerts(self, db, device):
        """Clear stale policy alerts when a device is authorized."""
        now = datetime.utcnow()
        q = db.query(Alert).filter(
            Alert.is_resolved == False,
            Alert.alert_type.in_(self.POLICY_ALERT_TYPES),
        )
        if device.mac_address:
            q = q.filter(
                (Alert.mac_address == device.mac_address)
                | (Alert.device_id == device.id)
            )
        else:
            q = q.filter(Alert.device_id == device.id)

        for alert in q.all():
            alert.is_resolved = True
            alert.resolved_at = now
            alert.resolved_by = 'system:authorized'

    # FIX: New helper to resolve alerts tied to a specific MAC address when
    # the device's MAC changes, preventing orphaned unresolved alerts.
    def _resolve_alerts_by_mac(self, db, old_mac, device_id):
        """Resolve open policy alerts keyed to an old MAC address."""
        now = datetime.utcnow()
        alerts = db.query(Alert).filter(
            Alert.is_resolved == False,
            Alert.alert_type.in_(self.POLICY_ALERT_TYPES),
            Alert.mac_address == old_mac,
        ).all()
        for alert in alerts:
            alert.is_resolved = True
            alert.resolved_at = now
            alert.resolved_by = 'system:mac_changed'
        if alerts:
            log.info(f"Resolved {len(alerts)} stale alert(s) for old MAC {old_mac}")

    def resolve_alerts_for_device_id(self, db, device_id):
        device = db.query(Device).get(device_id)
        if device:
            self._resolve_policy_alerts(db, device)

    def _validate_naming_convention(self, hostname):
        if not hostname or hostname.startswith('UNKNOWN'):
            return False, "Hostname is unknown or not resolvable"
        if not re.match(self.naming_pattern, hostname):
            return False, f"Hostname does not match pattern: {self.naming_description}"
        return True, "Hostname follows naming convention"

    def _send_email_alert(self, alert_title, alert_description, device_info):
        if not self.smtp_enabled or not self.smtp_user:
            return
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = self.admin_email
            msg['Subject'] = f"[UltraTech Network Alert] {alert_title}"
            body = f"""
            <html><body>
            <h2>{alert_title}</h2>
            <p>{alert_description}</p>
            <ul>
              <li>Hostname: {device_info.get('hostname')}</li>
              <li>IP: {device_info.get('ip_address')}</li>
              <li>MAC: {device_info.get('mac_address')}</li>
            </ul>
            </body></html>
            """
            msg.attach(MIMEText(body, 'html'))
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
            log.info(f"Email alert sent to {self.admin_email}")
        except Exception as e:
            log.error(f"Failed to send email alert: {e}")

    def _ping_host(self, ip):
        """Ping a single IP. Returns ip string if alive, None otherwise.

        FIX: Increased -w from 500ms to 1000ms and added one retry.
        The 500ms timeout caused inconsistent scan counts — devices like
        phones in sleep mode or Wi-Fi power-saving respond to the second
        ping but not the first. Two attempts with 1000ms each still
        completes a full /24 sweep in under 10s with 128 threads.
        """
        for _ in range(2):
            try:
                result = subprocess.run(
                    ['ping', '-n', '1', '-w', '1000', ip],
                    capture_output=True, text=True, timeout=3
                )
                if 'TTL=' in result.stdout or 'ttl=' in result.stdout:
                    return ip
            except Exception:
                pass
        return None

    def _read_arp_table(self):
        """Read the Windows ARP cache and return {ip: mac} dict.
        Called after the ping sweep so the cache is warm."""
        mac_map = {}
        try:
            result = subprocess.run(
                ['arp', '-a'], capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.split('\n'):
                parts = line.split()
                if len(parts) >= 2:
                    ip_candidate = parts[0]
                    mac_candidate = parts[1]
                    try:
                        ipaddress.ip_address(ip_candidate)
                        if '-' in mac_candidate and len(mac_candidate) == 17:
                            mac_map[ip_candidate] = normalize_mac(mac_candidate)
                    except (ipaddress.AddressValueError, ValueError):
                        continue
        except Exception as e:
            log.error(f"ARP table read failed: {e}")
        return mac_map

    def _scan_windows_arp(self):
        """Fast parallel ping sweep + ARP MAC lookup. No Admin rights required.

        Strategy:
          1. Enumerate all host IPs in the subnet.
          2. Ping them all concurrently (128 threads, 500ms timeout each).
          3. Read the ARP cache — now warm from the pings — to get MACs.
          4. Build device list from responding IPs that have a known MAC.

        A full /24 (254 hosts) completes in ~3-5 seconds instead of 60+.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        try:
            network = ipaddress.ip_network(self.network_range, strict=False)
            all_hosts = [str(ip) for ip in network.hosts()]
            log.info(f"Parallel ping sweep: {len(all_hosts)} hosts on {self.network_range}")

            # --- Phase 1: ping sweep (concurrent) ---
            alive_ips = set()
            max_workers = min(128, len(all_hosts))
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {pool.submit(self._ping_host, ip): ip for ip in all_hosts}
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        alive_ips.add(result)

            log.info(f"Ping sweep complete: {len(alive_ips)} host(s) responded")

            if not alive_ips:
                log.warning("No hosts responded to ping — ARP cache may be empty")
                return []

            # --- Phase 2: read ARP cache (now warm) ---
            mac_map = self._read_arp_table()

            # --- Phase 3: build device list ---
            devices = []
            for ip in sorted(alive_ips):
                if not self._is_ip_in_network_range(ip):
                    continue

                mac = mac_map.get(ip)
                if not mac:
                    # Host replied to ping but MAC not in ARP cache yet — skip
                    log.debug(f"No MAC in ARP cache for {ip}, skipping")
                    continue

                try:
                    hostname = socket.gethostbyaddr(ip)[0].split('.')[0].upper()
                except socket.herror:
                    hostname = f"UNKNOWN-{mac.replace(':', '-')}"

                fingerprint = self.fingerprinting.identify_device(mac, ip)
                devices.append({
                    'hostname': hostname,
                    'ip_address': ip,
                    'mac_address': mac,
                    'vendor': fingerprint.get('vendor', 'Unknown'),
                    'os': fingerprint.get('os', 'Unknown'),
                    'detected_at': datetime.utcnow().isoformat()
                })

            self.detected_devices = devices
            log.info(f"Scan complete: {len(devices)} device(s) found")
            return devices

        except Exception as e:
            log.error(f"Parallel ping sweep failed: {e}")
            return []
        except Exception as e:
            log.error(f"Windows ARP scan failed: {e}")
            return []

    def _update_trust_score(self, device):
        score = self.fingerprinting.calculate_trust_score(device)
        if device.is_quarantined:
            score = min(score, 10)
        elif not device.is_authorized:
            score = min(score, 45)
        elif device.certificates:
            active = [c for c in device.certificates if not c.is_revoked]
            if active:
                score = max(score, 85)
        device.trust_score = round(max(0, min(100, score)), 1)

    def _create_alert(self, db, alert_type, severity, title, description, ip, mac, device_id=None):
        mac = normalize_mac(mac)

        # FIX: Deduplicate by (mac_address OR device_id) + alert_type, not just
        # mac_address alone. This catches cases where mac is unknown/None but
        # device_id is known, preventing duplicate alerts for the same device
        # reached via different lookup paths.
        existing_query = db.query(Alert).filter(
            Alert.alert_type == alert_type,
            Alert.is_resolved == False,
        )
        if device_id:
            existing_query = existing_query.filter(
                (Alert.mac_address == mac) | (Alert.device_id == device_id)
            )
        else:
            existing_query = existing_query.filter(Alert.mac_address == mac)

        if existing_query.first():
            return None

        alert = Alert(
            device_id=device_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            ip_address=ip,
            mac_address=mac,
        )
        db.add(alert)
        self.alert_count += 1
        log.warning(f"Alert created: {title}")
        return alert

    def _emit_realtime(self, event, payload):
        if _socketio:
            try:
                _socketio.emit(event, payload)
            except Exception as e:
                log.error(f"Socket emit failed: {e}")

    def _demo_devices(self):
        # FIX: Removed random.sample() with randomized k — it was the direct
        # cause of scan results varying between runs. Now returns the full
        # deterministic pool every time, matching what a real scan would do.
        pool = [
            ("IT-WS-0042", "192.168.1.10", "00:11:22:33:44:55"),
            ("HR-LPT-0023", "192.168.1.11", "00:11:22:33:44:56"),
            ("UNKNOWN-1",   "192.168.1.50", "AA:BB:CC:DD:EE:FF"),
        ]
        return [
            {
                'hostname': h,
                'ip_address': ip,
                'mac_address': normalize_mac(mac),
                'vendor': 'Demo Vendor',
                'os': 'Unknown',
                'detected_at': datetime.utcnow().isoformat(),
            }
            for h, ip, mac in pool
        ]