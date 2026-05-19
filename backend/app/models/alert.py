from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from ..database import Base


class AlertSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(enum.Enum):
    HOSTNAME_CHANGE = "hostname_change"
    MAC_SPOOFING = "mac_spoofing"
    UNKNOWN_DEVICE = "unknown_device"
    DUPLICATE_IP = "duplicate_ip"
    CERT_MISMATCH = "cert_mismatch"
    CERT_EXPIRED = "cert_expired"
    CERT_REVOKED = "cert_revoked"
    AUTH_FAILURE = "auth_failure"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class Alert(Base):
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=True)
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    mac_address = Column(String(17), nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    device = relationship('Device', back_populates='alerts')

    def __repr__(self):
        return f"<Alert {self.alert_type.value} - {self.severity.value}>"
