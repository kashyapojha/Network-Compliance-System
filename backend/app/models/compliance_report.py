from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from ..database import Base


class ComplianceReport(Base):
    __tablename__ = 'compliance_reports'

    id = Column(Integer, primary_key=True, index=True)
    report_name = Column(String(200), nullable=False)
    report_type = Column(String(50), nullable=False)  # daily, weekly, monthly, on_demand
    total_devices = Column(Integer, nullable=False)
    authorized_devices = Column(Integer, nullable=False)
    unauthorized_devices = Column(Integer, nullable=False)
    compliant_devices = Column(Integer, nullable=False)
    non_compliant_devices = Column(Integer, nullable=False)
    compliance_score = Column(Float, nullable=False)
    alerts_generated = Column(Integer, nullable=False)
    auth_successes = Column(Integer, nullable=False)
    auth_failures = Column(Integer, nullable=False)
    summary = Column(Text, nullable=True)
    report_data = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ComplianceReport {self.report_name} - Score: {self.compliance_score}%>"
