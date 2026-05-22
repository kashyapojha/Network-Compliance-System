#!/usr/bin/env python3
"""
Certificate Validation Script for FreeRADIUS
Validates device certificates against the enterprise CA and database
"""

import sys
import os
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.backends import default_backend

# Resolve project root dynamically to locate dotenv and SQLite DB
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Load dotenv if python-dotenv is installed
try:
    from dotenv import load_dotenv
    if (PROJECT_ROOT / '.env').is_file():
        load_dotenv(PROJECT_ROOT / '.env', override=True)
    elif (PROJECT_ROOT / 'backend' / '.env').is_file():
        load_dotenv(PROJECT_ROOT / 'backend' / '.env', override=True)
except ImportError:
    # Manual dotenv parser fallback
    for dotenv_path in [PROJECT_ROOT / '.env', PROJECT_ROOT / 'backend' / '.env']:
        if dotenv_path.is_file():
            with open(dotenv_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        os.environ.setdefault(k.strip(), v.strip())
            break

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
    conn = None
    try:
        DATABASE_URL = os.getenv('DATABASE_URL', '')
        is_sqlite = False
        sqlite_db_path = None

        if DATABASE_URL.startswith('sqlite://'):
            is_sqlite = True
            db_path_str = DATABASE_URL.replace('sqlite:///', '').replace('sqlite://', '')
            path_obj = Path(db_path_str)
            if not path_obj.is_absolute():
                # Check current working directory first to align with SQLAlchemy relative path behavior
                if Path(path_obj).is_file():
                    sqlite_db_path = Path(path_obj).resolve()
                elif (PROJECT_ROOT / 'backend' / path_obj).is_file():
                    sqlite_db_path = PROJECT_ROOT / 'backend' / path_obj
                else:
                    sqlite_db_path = PROJECT_ROOT / path_obj
            else:
                sqlite_db_path = path_obj
        else:
            try:
                import psycopg2
            except ImportError:
                is_sqlite = True
                if Path('network_compliance.db').is_file():
                    sqlite_db_path = Path('network_compliance.db').resolve()
                elif (PROJECT_ROOT / 'backend' / 'network_compliance.db').is_file():
                    sqlite_db_path = PROJECT_ROOT / 'backend' / 'network_compliance.db'
                else:
                    sqlite_db_path = PROJECT_ROOT / 'network_compliance.db'

        # Connect to database
        if is_sqlite:
            import sqlite3
            conn = sqlite3.connect(str(sqlite_db_path))
        else:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
        cursor = conn.cursor()
        
        # Check certificate in database
        placeholder = '?' if is_sqlite else '%s'
        query = f"""
            SELECT c.is_revoked, c.not_valid_after, d.is_authorized, d.is_quarantined
            FROM certificates c
            JOIN devices d ON c.device_id = d.id
            WHERE c.serial_number = {placeholder}
        """
        cursor.execute(query, (serial_number,))
        result = cursor.fetchone()
        
        if not result:
            print(f"Certificate {serial_number} not found in database", file=sys.stderr)
            return 1
        
        is_revoked, not_valid_after, is_authorized, is_quarantined = result
        
        # Convert types safely for database differences
        is_revoked = bool(is_revoked)
        is_authorized = bool(is_authorized)
        is_quarantined = bool(is_quarantined)

        # Check if revoked
        if is_revoked:
            print(f"Certificate {serial_number} is revoked", file=sys.stderr)
            return 1
        
        # Check if expired
        from datetime import datetime
        if isinstance(not_valid_after, str):
            parsed_date = None
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                try:
                    parsed_date = datetime.strptime(not_valid_after, fmt)
                    break
                except ValueError:
                    continue
            if parsed_date is None:
                print(f"Could not parse datetime string: {not_valid_after}", file=sys.stderr)
                return 1
            not_valid_after = parsed_date

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
        if conn is not None:
            conn.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: validate_cert.py <serial_number>", file=sys.stderr)
        sys.exit(1)
    
    serial_number = sys.argv[1]
    exit_code = validate_certificate(serial_number)
    sys.exit(exit_code)
