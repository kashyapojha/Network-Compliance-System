from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.device import Device
from ..models.alert import Alert
from ..models.auth_log import AuthLog, AuthStatus
from ..models.compliance_report import ComplianceReport
from ..services.compliance_service import ComplianceService
from datetime import datetime, timedelta

bp = Blueprint('compliance', __name__)


@bp.route('/score', methods=['GET'])
def get_compliance_score():
    """Calculate current network compliance score."""
    db: Session = next(get_db())
    try:
        total_devices = db.query(Device).count()
        if total_devices == 0:
            return jsonify({'score': 100, 'total_devices': 0})
        
        authorized = db.query(Device).filter(Device.is_authorized == True).count()
        quarantined = db.query(Device).filter(Device.is_quarantined == True).count()
        
        # Calculate score based on authorization rate
        score = (authorized / total_devices) * 100
        
        return jsonify({
            'score': round(score, 2),
            'total_devices': total_devices,
            'authorized': authorized,
            'unauthorized': total_devices - authorized,
            'quarantined': quarantined
        })
    finally:
        db.close()


@bp.route('/report', methods=['POST'])
def generate_report():
    """Generate a compliance report."""
    db: Session = next(get_db())
    try:
        data = request.get_json()
        report_type = data.get('type', 'on_demand')
        
        compliance_service = ComplianceService()
        report = compliance_service.generate_report(report_type)
        
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
    """Get real-time compliance metrics."""
    db: Session = next(get_db())
    try:
        # Device metrics
        total_devices = db.query(Device).count()
        authorized_devices = db.query(Device).filter(Device.is_authorized == True).count()
        quarantined_devices = db.query(Device).filter(Device.is_quarantined == True).count()
        
        # Alert metrics (last 24 hours)
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
        
        return jsonify({
            'devices': {
                'total': total_devices,
                'authorized': authorized_devices,
                'unauthorized': total_devices - authorized_devices,
                'quarantined': quarantined_devices
            },
            'alerts': {
                'last_24h': recent_alerts
            },
            'authentication': {
                'success_last_24h': recent_auth_success,
                'failure_last_24h': recent_auth_failure
            }
        })
    finally:
        db.close()
