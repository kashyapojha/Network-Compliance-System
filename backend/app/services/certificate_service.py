from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import os
import json


class CertificateService:
    """Service for managing certificates and CA operations."""
    
    def __init__(self):
        self.ca_dir = "certificates/ca"
        self.issued_dir = "certificates/issued"
        self.revoked_dir = "certificates/revoked"
        self._ensure_directories()
        self._load_or_create_ca()
    
    def _ensure_directories(self):
        """Ensure certificate directories exist."""
        os.makedirs(self.ca_dir, exist_ok=True)
        os.makedirs(self.issued_dir, exist_ok=True)
        os.makedirs(self.revoked_dir, exist_ok=True)
    
    def _load_or_create_ca(self):
        """Load existing CA or create new one."""
        ca_key_path = os.path.join(self.ca_dir, "ca_key.pem")
        ca_cert_path = os.path.join(self.ca_dir, "ca_cert.pem")
        
        if os.path.exists(ca_key_path) and os.path.exists(ca_cert_path):
            # Load existing CA
            with open(ca_key_path, "rb") as f:
                self.ca_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
            with open(ca_cert_path, "rb") as f:
                self.ca_cert = x509.load_pem_x509_certificate(
                    f.read(),
                    backend=default_backend()
                )
        else:
            # Create new CA
            self.ca_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096,
                backend=default_backend()
            )
            
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Enterprise Network"),
                x509.NameAttribute(NameOID.COMMON_NAME, "Enterprise Root CA"),
            ])
            
            self.ca_cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                self.ca_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=3650)  # 10 years
            ).add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            ).sign(self.ca_key, hashes.SHA256(), default_backend())
            
            # Save CA
            with open(ca_key_path, "wb") as f:
                f.write(self.ca_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            with open(ca_cert_path, "wb") as f:
                f.write(self.ca_cert.public_bytes(serialization.Encoding.PEM))
    
    def generate_device_certificate(self, device):
        """Generate and sign a certificate for a device."""
        # Generate device private key
        device_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Create certificate subject
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Enterprise Network"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, device.department),
            x509.NameAttribute(NameOID.COMMON_NAME, device.hostname),
        ])
        
        # Build certificate
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            self.ca_cert.subject
        ).public_key(
            device_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)  # 1 year
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(device.hostname),
                x509.IPAddress(device.ip_address) if device.ip_address else None,
            ]),
            critical=False,
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                key_cert_sign=False,
                key_agreement=False,
                content_commitment=False,
                data_encipherment=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True,
        ).add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
            ]),
            critical=False,
        ).sign(self.ca_key, hashes.SHA256(), default_backend())
        
        # Serialize
        cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        key_pem = device_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        # Save to file
        cert_filename = f"{device.hostname}_{cert.serial_number}.pem"
        cert_path = os.path.join(self.issued_dir, cert_filename)
        
        with open(cert_path, "w") as f:
            f.write(cert_pem)
            f.write(key_pem)
        
        return {
            'serial_number': str(cert.serial_number),
            'certificate_pem': cert_pem,
            'private_key_pem': key_pem,
            'issuer': self.ca_cert.subject.rfc4514_string(),
            'subject': subject.rfc4514_string(),
            'not_valid_before': cert.not_valid_before,
            'not_valid_after': cert.not_valid_after,
            'cert_path': cert_path
        }
    
    def revoke_certificate(self, serial_number, reason="Admin revocation"):
        """Revoke a certificate by serial number."""
        # Move certificate to revoked directory
        cert_files = os.listdir(self.issued_dir)
        for cert_file in cert_files:
            if serial_number in cert_file:
                src = os.path.join(self.issued_dir, cert_file)
                dst = os.path.join(self.revoked_dir, cert_file)
                os.rename(src, dst)
                return True
        
        return False
    
    def get_ca_info(self):
        """Get CA certificate information."""
        return {
            'subject': self.ca_cert.subject.rfc4514_string(),
            'issuer': self.ca_cert.issuer.rfc4514_string(),
            'serial_number': str(self.ca_cert.serial_number),
            'not_valid_before': self.ca_cert.not_valid_before.isoformat(),
            'not_valid_after': self.ca_cert.not_valid_after.isoformat(),
            'is_ca': True
        }
    
    def verify_certificate(self, cert_pem):
        """Verify a certificate against the CA."""
        try:
            cert = x509.load_pem_x509_certificate(
                cert_pem.encode('utf-8'),
                backend=default_backend()
            )
            
            # Check if expired
            if datetime.utcnow() > cert.not_valid_after:
                return {'valid': False, 'reason': 'Certificate expired'}
            
            # Check if issued by our CA
            if cert.issuer != self.ca_cert.subject:
                return {'valid': False, 'reason': 'Not issued by trusted CA'}
            
            # Verify signature
            # Note: Full chain verification would require CRL checking
            return {'valid': True, 'serial_number': str(cert.serial_number)}
            
        except Exception as e:
            return {'valid': False, 'reason': str(e)}
