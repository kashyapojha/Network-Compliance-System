from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.device import Device
from ..models.alert import Alert
from ..models.auth_log import AuthLog, AuthStatus
from ..models.compliance_report import ComplianceReport
from ..utils.compliance_utils import calculate_compliance_score
import json


class ComplianceService:
    """Service for generating compliance reports and scores."""
    
    def generate_report(self, report_type='on_demand'):
        """Generate a compliance report."""
        db: Session = next(get_db())
        
        try:
            # Get metrics
            total_devices = db.query(Device).count()
            authorized_devices = db.query(Device).filter(
                Device.is_authorized == True
            ).count()
            unauthorized_devices = total_devices - authorized_devices
            
            quarantined_devices = db.query(Device).filter(
                Device.is_quarantined == True
            ).count()
            
            # Compliance based on certificate validity
            compliant_devices = authorized_devices  # Simplified
            non_compliant_devices = unauthorized_devices
            
            compliance_score, unresolved_alerts = calculate_compliance_score(db)

            # Alert metrics
            alerts_generated = db.query(Alert).count()
            
            # Auth metrics (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(hours=24)
            auth_successes = db.query(AuthLog).filter(
                AuthLog.created_at >= yesterday,
                AuthLog.status == AuthStatus.SUCCESS
            ).count()
            auth_failures = db.query(AuthLog).filter(
                AuthLog.created_at >= yesterday,
                AuthLog.status != AuthStatus.SUCCESS
            ).count()
            
            # Generate report name
            report_name = f"{report_type.capitalize()} Report - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            
            # Create summary
            summary = self._generate_summary(
                total_devices, authorized_devices, unauthorized_devices,
                quarantined_devices, compliance_score, alerts_generated
            )
            
            # Create report
            report = ComplianceReport(
                report_name=report_name,
                report_type=report_type,
                total_devices=total_devices,
                authorized_devices=authorized_devices,
                unauthorized_devices=unauthorized_devices,
                compliant_devices=compliant_devices,
                non_compliant_devices=non_compliant_devices,
                compliance_score=compliance_score,
                alerts_generated=alerts_generated,
                auth_successes=auth_successes,
                auth_failures=auth_failures,
                summary=summary,
                report_data=json.dumps({
                    'timestamp': datetime.utcnow().isoformat(),
                    'metrics': {
                        'devices': {
                            'total': total_devices,
                            'authorized': authorized_devices,
                            'unauthorized': unauthorized_devices,
                            'quarantined': quarantined_devices
                        },
                        'alerts': alerts_generated,
                        'authentication': {
                            'successes': auth_successes,
                            'failures': auth_failures
                        }
                    }
                })
            )
            
            db.add(report)
            db.commit()
            db.refresh(report)
            
            return report
            
        finally:
            db.close()
    
    def _generate_summary(self, total, authorized, unauthorized, quarantined, score, alerts):
        """Generate a human-readable summary."""
        summary_parts = []
        
        summary_parts.append(f"Total devices: {total}")
        summary_parts.append(f"Authorized: {authorized} ({authorized/total*100:.1f}%)" if total > 0 else "Authorized: 0")
        summary_parts.append(f"Unauthorized: {unauthorized}")
        summary_parts.append(f"Quarantined: {quarantined}")
        summary_parts.append(f"Compliance Score: {score:.1f}%")
        summary_parts.append(f"Total Alerts: {alerts}")
        
        if score >= 90:
            status = "Excellent"
        elif score >= 70:
            status = "Good"
        elif score >= 50:
            status = "Fair"
        else:
            status = "Poor"
        
        summary_parts.append(f"Overall Status: {status}")
        
        return " | ".join(summary_parts)
    
    def get_device_compliance(self, device_id):
        """Get compliance status for a specific device."""
        db: Session = next(get_db())
        
        try:
            device = db.query(Device).get(device_id)
            if not device:
                return None
            
            # Check certificate status
            has_valid_cert = any(
                not c.is_revoked and c.not_valid_after > datetime.utcnow()
                for c in device.certificates
            )
            
            # Check authorization
            is_authorized = device.is_authorized
            
            # Check quarantine
            is_quarantined = device.is_quarantined
            
            # Calculate compliance
            compliant = is_authorized and has_valid_cert and not is_quarantined
            
            return {
                'device_id': device.id,
                'hostname': device.hostname,
                'compliant': compliant,
                'authorized': is_authorized,
                'has_valid_certificate': has_valid_cert,
                'quarantined': is_quarantined,
                'trust_score': device.trust_score,
                'last_seen': device.last_seen.isoformat() if device.last_seen else None
            }
            
        finally:
            db.close()
