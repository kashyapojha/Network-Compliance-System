from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
import enum
from ..database import Base


class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    AUDITOR = "auditor"


class Admin(Base):
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Admin {self.username} ({self.role.value})>"
