import re
from typing import Tuple, List


def validate_mac_address(mac: str) -> bool:
    """Validate MAC address format."""
    pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    return bool(re.match(pattern, mac))


def validate_ip_address(ip: str) -> bool:
    """Validate IPv4 address format."""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    
    octets = ip.split('.')
    return all(0 <= int(octet) <= 255 for octet in octets)


def validate_hostname(hostname: str) -> Tuple[bool, List[str]]:
    """
    Validate hostname according to enterprise naming convention.
    Format: DEPT-TYPE-NNNN
    Returns (is_valid, list_of_errors)
    """
    errors = []
    
    if not hostname:
        errors.append("Hostname cannot be empty")
        return False, errors
    
    # Check format
    pattern = r'^([A-Z]{2,3})-([A-Z]{2,4})-(\d{4})$'
    if not re.match(pattern, hostname):
        errors.append("Hostname must follow format: DEPT-TYPE-NNNN (e.g., IT-WS-0042)")
    
    # Check length
    if len(hostname) < 10 or len(hostname) > 20:
        errors.append("Hostname must be between 10 and 20 characters")
    
    # Check uppercase
    if hostname != hostname.upper():
        errors.append("Hostname must be uppercase")
    
    # Validate department prefix
    valid_depts = ['IT', 'HR', 'FIN', 'OPS', 'DEV', 'MKT']
    dept = hostname.split('-')[0] if '-' in hostname else ''
    if dept not in valid_depts:
        errors.append(f"Invalid department prefix. Must be one of: {', '.join(valid_depts)}")
    
    # Validate device type
    valid_types = ['WS', 'LPT', 'SRV', 'PRN', 'MOB', 'CAM', 'IOT']
    dev_type = hostname.split('-')[1] if len(hostname.split('-')) > 1 else ''
    if dev_type not in valid_types:
        errors.append(f"Invalid device type. Must be one of: {', '.join(valid_types)}")
    
    return len(errors) == 0, errors


def validate_certificate_pem(pem: str) -> bool:
    """Validate PEM certificate format."""
    if not pem:
        return False
    
    pem = pem.strip()
    return pem.startswith('-----BEGIN CERTIFICATE-----') and pem.endswith('-----END CERTIFICATE-----')


def sanitize_input(input_str: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not input_str:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')']
    for char in dangerous_chars:
        input_str = input_str.replace(char, '')
    
    return input_str.strip()
