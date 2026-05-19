from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base


class Certificate(Base):
    __tablename__ = 'certificates'

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    serial_number = Column(String(64), unique=True, nullable=False, index=True)
    certificate_pem = Column(Text, nullable=False)
    private_key_pem = Column(Text, nullable=False)
    issuer = Column(String(100), nullable=False)
    subject = Column(String(100), nullable=False)
    not_valid_before = Column(DateTime, nullable=False)
    not_valid_after = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    device = relationship('Device', back_populates='certificates')

    def __repr__(self):
        return f"<Certificate {self.serial_number} for Device {self.device_id}>"
