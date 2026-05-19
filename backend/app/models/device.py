from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class Device(Base):
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(100), unique=True, nullable=False, index=True)
    mac_address = Column(String(17), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    device_type = Column(String(50), nullable=False)  # WS, LPT, SRV, PRN, MOB, CAM, IOT
    department = Column(String(50), nullable=False)  # IT, HR, FIN, OPS, DEV, MKT
    os_fingerprint = Column(String(100), nullable=True)
    vendor = Column(String(100), nullable=True)
    trust_score = Column(Float, default=100.0)
    is_authorized = Column(Boolean, default=False)
    is_quarantined = Column(Boolean, default=False)
    vlan_assignment = Column(Integer, nullable=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    certificates = relationship('Certificate', back_populates='device', cascade='all, delete-orphan')
    auth_logs = relationship('AuthLog', back_populates='device', cascade='all, delete-orphan')
    alerts = relationship('Alert', back_populates='device', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Device {self.hostname} ({self.mac_address})>"
