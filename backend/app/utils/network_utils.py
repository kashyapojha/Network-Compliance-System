"""Utilities to detect local network interface, IP, MAC, and subnet."""
import ipaddress
import socket
import uuid


def get_local_ip():
    """Return the primary local IPv4 address used for outbound traffic."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
    except OSError:
        return socket.gethostbyname(socket.gethostname())


def get_mac_address():
    """Return local MAC address in AA:BB:CC:DD:EE:FF format."""
    node = uuid.getnode()
    if (node >> 40) & 1:
        return None
    mac = ':'.join(f'{(node >> i) & 0xff:02x}' for i in range(40, -8, -8))
    return mac.upper()


def get_network_cidr(ip=None, prefix_len=24):
    """Build a CIDR string (e.g. 192.168.0.0/24) from the local IP."""
    ip = ip or get_local_ip()
    network = ipaddress.ip_network(f'{ip}/{prefix_len}', strict=False)
    return str(network)


def get_local_network_info():
    """Collect local network details for UI and monitoring."""
    ip = get_local_ip()
    mac = get_mac_address()
    cidr = get_network_cidr(ip)
    hostname = socket.gethostname().split('.')[0].upper()

    return {
        'hostname': hostname,
        'ip_address': ip,
        'mac_address': mac,
        'network_range': cidr,
    }


def normalize_mac(mac):
    """Normalize MAC to uppercase colon-separated format."""
    if not mac:
        return mac
    mac = mac.strip().upper().replace('-', ':')
    parts = mac.split(':')
    if len(parts) == 6:
        return ':'.join(p.zfill(2) for p in parts)
    return mac
