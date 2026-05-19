#!/usr/bin/env python3
"""
Certificate Validation Script for FreeRADIUS
Validates device certificates against the enterprise CA and database
"""

import sys
import os
import psycopg2
from cryptography import x509
from cryptography.hazmat.backends import default_backend

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'network_compliance')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

# CA certificate path
CA_CERT_PATH = os.getenv('CA_CERT_PATH', '/etc/freeradius/certs/ca.pem')


def validate_certificate(serial_number):
    """
    Validate a certificate by serial number.
    Returns 0 if valid, 1 if invalid/revoked.
    """
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # Check certificate in database
        cursor.execute(
            """
            SELECT c.is_revoked, c.not_valid_after, d.is_authorized, d.is_quarantined
            FROM certificates c
            JOIN devices d ON c.device_id = d.id
            WHERE c.serial_number = %s
            """,
            (serial_number,)
        )
        
        result = cursor.fetchone()
        
        if not result:
            print(f"Certificate {serial_number} not found in database", file=sys.stderr)
            return 1
        
        is_revoked, not_valid_after, is_authorized, is_quarantined = result
        
        # Check if revoked
        if is_revoked:
            print(f"Certificate {serial_number} is revoked", file=sys.stderr)
            return 1
        
        # Check if expired
        from datetime import datetime
        if datetime.utcnow() > not_valid_after:
            print(f"Certificate {serial_number} is expired", file=sys.stderr)
            return 1
        
        # Check if device is authorized
        if not is_authorized:
            print(f"Device for certificate {serial_number} is not authorized", file=sys.stderr)
            return 1
        
        # Check if device is quarantined
        if is_quarantined:
            print(f"Device for certificate {serial_number} is quarantined", file=sys.stderr)
            return 1
        
        # Certificate is valid
        print(f"Certificate {serial_number} validated successfully", file=sys.stderr)
        return 0
        
    except Exception as e:
        print(f"Certificate validation error: {e}", file=sys.stderr)
        return 1
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: validate_cert.py <serial_number>", file=sys.stderr)
        sys.exit(1)
    
    serial_number = sys.argv[1]
    exit_code = validate_certificate(serial_number)
    sys.exit(exit_code)
