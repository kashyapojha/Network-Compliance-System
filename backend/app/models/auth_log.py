from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum
from ..database import Base


class AuthStatus(enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    CERT_REVOKED = "cert_revoked"
    CERT_EXPIRED = "cert_expired"
    CERT_INVALID = "cert_invalid"
    DEVICE_UNAUTHORIZED = "device_unauthorized"
    MAC_MISMATCH = "mac_mismatch"


class AuthLog(Base):
    __tablename__ = 'authentication_logs'

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=True)
    username = Column(String(100), nullable=True)
    mac_address = Column(String(17), nullable=True)
    ip_address = Column(String(45), nullable=True)
    certificate_serial = Column(String(64), nullable=True)
    auth_method = Column(String(50), nullable=False)  # EAP-TLS, EAP-PEAP, etc.
    status = Column(Enum(AuthStatus), nullable=False)
    failure_reason = Column(Text, nullable=True)
    nas_ip_address = Column(String(45), nullable=True)
    nas_port = Column(Integer, nullable=True)
    session_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    device = relationship('Device', back_populates='auth_logs')

    def __repr__(self):
        return f"<AuthLog {self.status.value} for {self.mac_address}>"
