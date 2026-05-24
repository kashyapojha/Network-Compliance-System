from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.device import Device
from ..models.alert import Alert
from ..models.auth_log import AuthLog, AuthStatus
from ..models.compliance_report import ComplianceReport
from ..utils.compliance_utils import calculate_compliance_score
import ipaddress
import json


def _ip_in_network(ip, cidr):
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
    except Exception:
        return False


class ComplianceService:
    """Service for generating compliance reports and scores."""

    def generate_report(self, report_type='on_demand', network_range=None):
        """Generate a compliance report.
        FIX: accepts network_range so the stored compliance_score in the report
        reflects the current network, not all historical alerts globally.
        """
        db: Session = next(get_db())
        try:
            total_devices = db.query(Device).count()
            authorized_devices = db.query(Device).filter(Device.is_authorized == True).count()
            unauthorized_devices = total_devices - authorized_devices
            quarantined_devices = db.query(Device).filter(Device.is_quarantined == True).count()

            compliant_devices = authorized_devices
            non_compliant_devices = unauthorized_devices

            # FIX: filter unresolved alerts by network range if provided
            all_unresolved = db.query(Alert).filter(Alert.is_resolved == False).all()
            if network_range:
                network_unresolved_count = len([
                    a for a in all_unresolved
                    if a.ip_address and _ip_in_network(a.ip_address, network_range)
                ])
            else:
                network_unresolved_count = len(all_unresolved)

            compliance_score, _ = calculate_compliance_score(
                db, network_unresolved=network_unresolved_count
            )

            alerts_generated = db.query(Alert).count()

            yesterday = datetime.utcnow() - timedelta(hours=24)
            auth_successes = db.query(AuthLog).filter(
                AuthLog.created_at >= yesterday,
                AuthLog.status == AuthStatus.SUCCESS
            ).count()
            auth_failures = db.query(AuthLog).filter(
                AuthLog.created_at >= yesterday,
                AuthLog.status != AuthStatus.SUCCESS
            ).count()

            report_name = f"{report_type.capitalize()} Report - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            if network_range:
                report_name += f" [{network_range}]"

            summary = self._generate_summary(
                total_devices, authorized_devices, unauthorized_devices,
                quarantined_devices, compliance_score, alerts_generated
            )

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
                    'network_range': network_range,
                    'metrics': {
                        'devices': {
                            'total': total_devices,
                            'authorized': authorized_devices,
                            'unauthorized': unauthorized_devices,
                            'quarantined': quarantined_devices
                        },
                        'alerts': alerts_generated,
                        'unresolved_network': network_unresolved_count,
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
        summary_parts = [
            f"Total devices: {total}",
            f"Authorized: {authorized} ({authorized/total*100:.1f}%)" if total > 0 else "Authorized: 0",
            f"Unauthorized: {unauthorized}",
            f"Quarantined: {quarantined}",
            f"Compliance Score: {score:.1f}%",
            f"Total Alerts: {alerts}",
            f"Overall Status: {'Excellent' if score >= 90 else 'Good' if score >= 70 else 'Fair' if score >= 50 else 'Poor'}"
        ]
        return " | ".join(summary_parts)

    def get_device_compliance(self, device_id):
        db: Session = next(get_db())
        try:
            device = db.query(Device).get(device_id)
            if not device:
                return None
            has_valid_cert = any(
                not c.is_revoked and c.not_valid_after > datetime.utcnow()
                for c in device.certificates
            )
            compliant = device.is_authorized and has_valid_cert and not device.is_quarantined
            return {
                'device_id': device.id,
                'hostname': device.hostname,
                'compliant': compliant,
                'authorized': device.is_authorized,
                'has_valid_certificate': has_valid_cert,
                'quarantined': device.is_quarantined,
                'trust_score': device.trust_score,
                'last_seen': device.last_seen.isoformat() if device.last_seen else None
            }
        finally:
            db.close()