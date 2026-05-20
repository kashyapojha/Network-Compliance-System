import threading
import time
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from scapy.all import ARP, Ether, srp, getmacbyip
from scapy.layers.l2 import getmacbyip
import socket
import hashlib
from ..database import get_db
from ..models.device import Device
from ..models.alert import Alert, AlertSeverity, AlertType
from ..services.fingerprinting_service import FingerprintingService
from ..utils.network_utils import get_network_cidr, normalize_mac
import os

log = logging.getLogger(__name__)


class MonitoringService:
    """Network monitoring service for compliance checking."""
    
    def __init__(self, network_range=None, poll_interval=30):
        self.network_range = (
            network_range
            or os.getenv('NETWORK_RANGE')
            or get_network_cidr()
        )
        self.poll_interval = poll_interval
        self.is_running = False
        self.detected_devices = []
        self.alert_count = 0
        self.fingerprinting = FingerprintingService()
        self._thread = None
    
    def start(self):
        """Start the monitoring loop."""
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
        """Stop the monitoring loop."""
        self.is_running = False
        log.info("Stopping network monitoring")
    
    def scan_network(self):
        """Scan network for active devices using ARP."""
        try:
            log.info(f"Scanning network: {self.network_range}")
            arp = ARP(pdst=self.network_range)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            result, _ = srp(ether / arp, timeout=3, verbose=False)
            
            devices = []
            for _, rcv in result:
                ip = rcv.psrc
                mac = rcv.hwsrc
                
                # Try to get hostname
                try:
                    hostname = socket.gethostbyaddr(ip)[0].split(".")[0].upper()
                except socket.herror:
                    hostname = f"UNKNOWN-{mac.replace(':', '-')}"
                
                # Get device fingerprint
                fingerprint = self.fingerprinting.identify_device(mac, ip)
                
                devices.append({
                    'hostname': hostname,
                    'ip_address': ip,
                    'mac_address': normalize_mac(mac),
                    'vendor': fingerprint.get('vendor', 'Unknown'),
                    'os': fingerprint.get('os', 'Unknown'),
                    'detected_at': datetime.utcnow().isoformat()
                })
            
            self.detected_devices = devices
            log.info(f"Detected {len(devices)} devices")
            return devices
            
        except ImportError:
            log.warning("Scapy not installed - using demo mode")
            return self._demo_devices()
        except Exception as e:
            log.error(f"Network scan failed: {e}")
            return []
    
    def scan_and_check(self):
        """Scan network and check compliance. Returns list of detected devices."""
        devices = self.scan_network()
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
        return devices
    
    def _check_device_compliance(self, db, device_data):
        """Check if a device is compliant with network policies."""
        mac = normalize_mac(device_data['mac_address'])
        ip = device_data['ip_address']
        hostname = device_data['hostname']
        
        # Check if device exists in database
        existing_device = db.query(Device).filter(
            Device.mac_address == mac
        ).first()
        
        if not existing_device:
            # Unknown device detected
            self._create_alert(
                db,
                AlertType.UNKNOWN_DEVICE,
                AlertSeverity.HIGH,
                f"Unknown device detected: {hostname}",
                f"Device with MAC {mac} and IP {ip} is not registered",
                ip,
                mac
            )
            return

        # Update last seen and trust score
        existing_device.last_seen = datetime.utcnow()
        existing_device.ip_address = ip
        self._update_trust_score(existing_device)
        
        # Check for hostname change
        if existing_device.hostname != hostname:
            self._create_alert(
                db,
                AlertType.HOSTNAME_CHANGE,
                AlertSeverity.MEDIUM,
                f"Hostname changed for device {existing_device.hostname}",
                f"Device changed from {existing_device.hostname} to {hostname}",
                ip,
                mac
            )
            existing_device.hostname = hostname
        
        # Check for MAC spoofing (IP changed but MAC same on different device)
        ip_device = db.query(Device).filter(
            Device.ip_address == ip,
            Device.mac_address != mac
        ).first()
        
        if ip_device:
            self._create_alert(
                db,
                AlertType.MAC_SPOOFING,
                AlertSeverity.CRITICAL,
                f"Potential MAC spoofing detected",
                f"IP {ip} now associated with different MAC {mac}",
                ip,
                mac
            )
        
        # Check for duplicate IP
        duplicate_ip = db.query(Device).filter(
            Device.ip_address == ip,
            Device.mac_address != mac
        ).count()
        
        if duplicate_ip > 0:
            self._create_alert(
                db,
                AlertType.DUPLICATE_IP,
                AlertSeverity.HIGH,
                f"Duplicate IP address detected",
                f"IP {ip} is assigned to multiple devices",
                ip,
                mac
            )
        
        # Check if device is authorized
        if not existing_device.is_authorized:
            self._create_alert(
                db,
                AlertType.SUSPICIOUS_ACTIVITY,
                AlertSeverity.MEDIUM,
                f"Unauthorized device on network",
                f"Device {hostname} is not authorized",
                ip,
                mac,
                device_id=existing_device.id
            )
            self._update_trust_score(existing_device)

    def _update_trust_score(self, device):
        """Recalculate trust score from authorization and device profile."""
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
        """Create an alert in the database (skip duplicate unresolved alerts)."""
        mac = normalize_mac(mac)
        existing = db.query(Alert).filter(
            Alert.mac_address == mac,
            Alert.alert_type == alert_type,
            Alert.is_resolved == False
        ).first()
        if existing:
            return

        alert = Alert(
            device_id=device_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            ip_address=ip,
            mac_address=mac
        )
        db.add(alert)
        self.alert_count += 1
        log.warning(f"Alert created: {title}")
    
    def _demo_devices(self):
        """Return demo devices for testing without network access."""
        import random
        pool = [
            ("IT-WS-0042", "192.168.1.10", "00:11:22:33:44:55"),
            ("HR-LPT-0023", "192.168.1.11", "00:11:22:33:44:56"),
            ("UNKNOWN-1", "192.168.1.50", "AA:BB:CC:DD:EE:FF"),
        ]
        seen = random.sample(pool, k=random.randint(2, 3))
        return [
            {
                'hostname': h,
                'ip_address': ip,
                'mac_address': mac,
                'vendor': 'Demo Vendor',
                'os': 'Unknown',
                'detected_at': datetime.utcnow().isoformat()
            }
            for h, ip, mac in seen
        ]
