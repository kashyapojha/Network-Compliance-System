import socket
import struct
import logging
from scapy.all import sr1, IP, TCP, ICMP
from scapy.layers.inet import TCP, IP

log = logging.getLogger(__name__)


class FingerprintingService:
    """Service for device fingerprinting and OS detection."""
    
    # MAC OUI prefixes for common vendors
    VENDOR_OUI = {
        '00:00:0C': 'Cisco',
        '00:50:56': 'VMware',
        '00:0C:29': 'VMware',
        '00:1A:4A': 'Intel',
        '00:15:5D': 'Microsoft',
        '00:1B:21': 'Intel',
        '00:E0:4C': 'Realtek',
        '00:11:22': 'Unknown',
        'AA:BB:CC': 'Demo',
    }
    
    # TCP/IP fingerprinting patterns
    OS_FINGERPRINTS = {
        'Windows': {
            'ttl': 128,
            'window_size': 8192,
            'flags': 'SA'
        },
        'Linux': {
            'ttl': 64,
            'window_size': 5840,
            'flags': 'SA'
        },
        'macOS': {
            'ttl': 64,
            'window_size': 65535,
            'flags': 'SA'
        },
        'Cisco IOS': {
            'ttl': 255,
            'window_size': 4128,
            'flags': 'SA'
        }
    }
    
    def identify_device(self, mac_address, ip_address):
        """Identify device vendor and OS using fingerprinting."""
        fingerprint = {
            'vendor': self._get_vendor_from_mac(mac_address),
            'os': 'Unknown',
            'confidence': 'low'
        }
        
        try:
            # Try OS fingerprinting
            os_info = self._fingerprint_os(ip_address)
            if os_info:
                fingerprint.update(os_info)
        except Exception as e:
            log.warning(f"OS fingerprinting failed for {ip_address}: {e}")
        
        return fingerprint
    
    def _get_vendor_from_mac(self, mac_address):
        """Get vendor from MAC address OUI."""
        oui = mac_address[:8].upper()
        return self.VENDOR_OUI.get(oui, 'Unknown')
    
    def _fingerprint_os(self, ip_address):
        """Fingerprint OS using TCP/IP stack analysis."""
        try:
            # Send TCP SYN packet
            packet = IP(dst=ip_address) / TCP(dport=80, flags='S')
            response = sr1(packet, timeout=2, verbose=False)
            
            if response and response.haslayer(TCP):
                tcp = response.getlayer(TCP)
                ip = response.getlayer(IP)
                
                ttl = ip.ttl
                window = tcp.window
                flags = tcp.flags
                
                # Match against known fingerprints
                for os_name, pattern in self.OS_FINGERPRINTS.items():
                    if (abs(ttl - pattern['ttl']) <= 32 and
                        window == pattern['window_size'] and
                        flags == pattern['flags']):
                        return {
                            'os': os_name,
                            'confidence': 'high',
                            'ttl': ttl,
                            'window_size': window
                        }
            
            return None
            
        except ImportError:
            log.warning("Scapy not available for OS fingerprinting")
            return None
        except Exception as e:
            log.error(f"OS fingerprinting error: {e}")
            return None
    
    def dhcp_fingerprint(self, dhcp_options):
        """Fingerprint device from DHCP options."""
        # This would analyze DHCP option 60 (Vendor Class Identifier)
        # and option 77 (User Class) to identify device type
        vendor_class = dhcp_options.get(60, '')
        
        if 'MSFT' in vendor_class:
            return 'Windows'
        elif 'Apple' in vendor_class:
            return 'macOS'
        elif 'android' in vendor_class.lower():
            return 'Android'
        else:
            return 'Unknown'
    
    def calculate_trust_score(self, device):
        """Calculate trust score for a device based on various factors."""
        score = 100.0
        
        # Deduct for unknown vendor
        if device.vendor == 'Unknown':
            score -= 20
        
        # Deduct for unknown OS
        if device.os_fingerprint == 'Unknown':
            score -= 15
        
        # Deduct for recent hostname changes
        # (would need to track history)
        
        # Deduct for failed authentication attempts
        # (would need to query auth logs)
        
        return max(0, min(100, score))
