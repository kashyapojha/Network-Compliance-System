from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.alert import Alert, AlertSeverity, AlertType
from ..models.device import Device
from datetime import datetime

bp = Blueprint('alerts', __name__)


@bp.route('/', methods=['GET'])
def list_alerts():
    """List all alerts with optional filtering."""
    db: Session = next(get_db())
    try:
        query = db.query(Alert)
        
        # Filter parameters
        if request.args.get('severity'):
            query = query.filter(Alert.severity == AlertSeverity[request.args.get('severity').upper()])
        if request.args.get('type'):
            query = query.filter(Alert.alert_type == AlertType[request.args.get('type').upper()])
        if request.args.get('resolved'):
            query = query.filter(Alert.is_resolved == (request.args.get('resolved') == 'true'))
        
        alerts = query.order_by(Alert.created_at.desc()).limit(100).all()
        
        result = []
        for a in alerts:
            result.append({
                'id': a.id,
                'device_id': a.device_id,
                'device_hostname': a.device.hostname if a.device else None,
                'alert_type': a.alert_type.value if a.alert_type else None,
                'severity': a.severity.value if a.severity else 'medium',
                'title': a.title or 'Alert',
                'description': a.description or '',
                'ip_address': a.ip_address,
                'mac_address': a.mac_address,
                'is_resolved': bool(a.is_resolved),
                'resolved_at': a.resolved_at.isoformat() if a.resolved_at else None,
                'resolved_by': a.resolved_by,
                'created_at': a.created_at.isoformat() if a.created_at else None
            })
        return jsonify(result)
    finally:
        db.close()


@bp.route('/', methods=['POST'])
def create_alert():
    """Create a new alert (typically called by monitoring system)."""
    db: Session = next(get_db())
    try:
        data = request.get_json()
        
        alert = Alert(
            device_id=data.get('device_id'),
            alert_type=AlertType[data.get('alert_type', 'SUSPICIOUS_ACTIVITY').upper()],
            severity=AlertSeverity[data.get('severity', 'MEDIUM').upper()],
            title=data.get('title', 'Alert'),
            description=data.get('description'),
            ip_address=data.get('ip_address'),
            mac_address=data.get('mac_address')
        )
        
        db.add(alert)
        db.commit()
        
        return jsonify({'id': alert.id, 'message': 'Alert created'}), 201
    finally:
        db.close()


@bp.route('/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve an alert."""
    db: Session = next(get_db())
    try:
        data = request.get_json()
        alert = db.query(Alert).get(alert_id)
        
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = data.get('resolved_by', 'admin')
        db.commit()
        
        return jsonify({'message': 'Alert resolved'})
    finally:
        db.close()


@bp.route('/stats', methods=['GET'])
def alert_stats():
    """Get alert statistics."""
    db: Session = next(get_db())
    try:
        total = db.query(Alert).count()
        unresolved = db.query(Alert).filter(Alert.is_resolved == False).count()
        critical = db.query(Alert).filter(
            Alert.severity == AlertSeverity.CRITICAL,
            Alert.is_resolved == False
        ).count()
        
        return jsonify({
            'total': total,
            'unresolved': unresolved,
            'critical': critical,
            'resolved': total - unresolved
        })
    finally:
        db.close()
