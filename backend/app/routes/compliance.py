from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.device import Device
from ..models.alert import Alert
from ..models.auth_log import AuthLog, AuthStatus
from ..models.compliance_report import ComplianceReport
from ..services.compliance_service import ComplianceService
from ..utils.compliance_utils import calculate_compliance_score
from datetime import datetime, timedelta
import ipaddress

bp = Blueprint('compliance', __name__)


def _ip_in_network(ip, cidr):
    """Return True if ip falls within the given CIDR range."""
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
    except Exception:
        return False


@bp.route('/score', methods=['GET'])
def get_compliance_score():
    """Calculate current network compliance score.
    FIX: accepts optional ?network_range param to scope alert count to current subnet.
    """
    db: Session = next(get_db())
    try:
        network_range = request.args.get('network_range')
        total_devices = db.query(Device).count()
        authorized = db.query(Device).filter(Device.is_authorized == True).count()
        quarantined = db.query(Device).filter(Device.is_quarantined == True).count()

        all_unresolved = db.query(Alert).filter(Alert.is_resolved == False).all()
        if network_range:
            network_unresolved = len([
                a for a in all_unresolved
                if a.ip_address and _ip_in_network(a.ip_address, network_range)
            ])
        else:
            network_unresolved = len(all_unresolved)

        score, _ = calculate_compliance_score(db, network_unresolved=network_unresolved)

        return jsonify({
            'score': score,
            'total_devices': total_devices,
            'authorized': authorized,
            'unauthorized': total_devices - authorized,
            'quarantined': quarantined,
            'unresolved_alerts': network_unresolved
        })
    finally:
        db.close()


@bp.route('/report', methods=['POST'])
def generate_report():
    """Generate a compliance report.
    FIX: passes network_range to service so report score is network-scoped.
    """
    db: Session = next(get_db())
    try:
        data = request.get_json()
        report_type = data.get('type', 'on_demand')
        network_range = data.get('network_range')

        compliance_service = ComplianceService()
        report = compliance_service.generate_report(report_type, network_range=network_range)

        return jsonify({
            'id': report.id,
            'report_name': report.report_name,
            'compliance_score': report.compliance_score,
            'total_devices': report.total_devices,
            'authorized_devices': report.authorized_devices,
            'unauthorized_devices': report.unauthorized_devices,
            'alerts_generated': report.alerts_generated,
            'created_at': report.created_at.isoformat()
        }), 201
    finally:
        db.close()


@bp.route('/reports', methods=['GET'])
def list_reports():
    """List all compliance reports."""
    db: Session = next(get_db())
    try:
        reports = db.query(ComplianceReport).order_by(
            ComplianceReport.created_at.desc()
        ).limit(20).all()

        return jsonify([{
            'id': r.id,
            'report_name': r.report_name,
            'report_type': r.report_type,
            'compliance_score': r.compliance_score,
            'total_devices': r.total_devices,
            'created_at': r.created_at.isoformat()
        } for r in reports])
    finally:
        db.close()


@bp.route('/reports/<int:report_id>', methods=['GET'])
def get_report(report_id):
    """Get detailed compliance report."""
    db: Session = next(get_db())
    try:
        report = db.query(ComplianceReport).get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404

        return jsonify({
            'id': report.id,
            'report_name': report.report_name,
            'report_type': report.report_type,
            'total_devices': report.total_devices,
            'authorized_devices': report.authorized_devices,
            'unauthorized_devices': report.unauthorized_devices,
            'compliant_devices': report.compliant_devices,
            'non_compliant_devices': report.non_compliant_devices,
            'compliance_score': report.compliance_score,
            'alerts_generated': report.alerts_generated,
            'auth_successes': report.auth_successes,
            'auth_failures': report.auth_failures,
            'summary': report.summary,
            'created_at': report.created_at.isoformat()
        })
    finally:
        db.close()


@bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get real-time compliance metrics.

    FIX: Accepts an optional ?network_range=x.x.x.x/24 query parameter.
    When provided, unresolved_alerts and compliance score are calculated
    only for alerts whose ip_address falls within that subnet — so the
    Dashboard counter matches what the Alerts page shows for the same network.
    Device counts are global (not per-network) since devices are registered
    independently of which network the backend is currently on.
    """
    db: Session = next(get_db())
    try:
        network_range = request.args.get('network_range')

        # Device metrics — always global
        total_devices = db.query(Device).count()
        authorized_devices = db.query(Device).filter(Device.is_authorized == True).count()
        quarantined_devices = db.query(Device).filter(Device.is_quarantined == True).count()

        # Alert metrics
        yesterday = datetime.utcnow() - timedelta(hours=24)
        recent_alerts = db.query(Alert).filter(Alert.created_at >= yesterday).count()

        # Auth metrics (last 24 hours)
        recent_auth_success = db.query(AuthLog).filter(
            AuthLog.created_at >= yesterday,
            AuthLog.status == AuthStatus.SUCCESS
        ).count()
        recent_auth_failure = db.query(AuthLog).filter(
            AuthLog.created_at >= yesterday,
            AuthLog.status != AuthStatus.SUCCESS
        ).count()

        # FIX: Filter unresolved alerts by network range when provided.
        # Fetch all unresolved and filter in Python using _ip_in_network(),
        # since SQLite doesn't have native CIDR functions.
        all_unresolved = db.query(Alert).filter(Alert.is_resolved == False).all()

        if network_range:
            network_unresolved = [
                a for a in all_unresolved
                if a.ip_address and _ip_in_network(a.ip_address, network_range)
            ]
        else:
            network_unresolved = all_unresolved

        unresolved_count = len(network_unresolved)

        # FIX: pass network-filtered count so the score matches the Alerts page
        compliance_score, _ = calculate_compliance_score(
            db,
            network_unresolved=unresolved_count
        )

        return jsonify({
            'devices': {
                'total': total_devices,
                'authorized': authorized_devices,
                'unauthorized': total_devices - authorized_devices,
                'quarantined': quarantined_devices
            },
            'alerts': {
                'last_24h': recent_alerts,
                'unresolved': unresolved_count
            },
            'compliance': {
                'score': compliance_score,
                'unresolved_alerts': unresolved_count
            },
            'authentication': {
                'success_last_24h': recent_auth_success,
                'failure_last_24h': recent_auth_failure
            }
        })
    finally:
        db.close()