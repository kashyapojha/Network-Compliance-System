from flask import Blueprint, request, jsonify
from flask_socketio import emit
from ..services.monitoring_service import MonitoringService
import threading

bp = Blueprint('monitoring', __name__)
monitoring_service = None
monitoring_thread = None


@bp.route('/start', methods=['POST'])
def start_monitoring():
    """Start the network monitoring service."""
    global monitoring_service, monitoring_thread
    
    if monitoring_service and monitoring_service.is_running:
        return jsonify({'message': 'Monitoring already running'})
    
    monitoring_service = MonitoringService()
    monitoring_thread = threading.Thread(target=monitoring_service.start)
    monitoring_thread.daemon = True
    monitoring_thread.start()
    
    return jsonify({'message': 'Monitoring started'})


@bp.route('/stop', methods=['POST'])
def stop_monitoring():
    """Stop the network monitoring service."""
    global monitoring_service
    
    if monitoring_service:
        monitoring_service.stop()
        monitoring_service = None
    
    return jsonify({'message': 'Monitoring stopped'})


@bp.route('/status', methods=['GET'])
def monitoring_status():
    """Get monitoring service status."""
    global monitoring_service
    
    if monitoring_service:
        return jsonify({
            'running': monitoring_service.is_running,
            'devices_detected': len(monitoring_service.detected_devices),
            'alerts_generated': monitoring_service.alert_count
        })
    
    return jsonify({'running': False})


@bp.route('/devices', methods=['GET'])
def get_detected_devices():
    """Get currently detected devices."""
    global monitoring_service
    
    if monitoring_service:
        return jsonify(monitoring_service.detected_devices)
    
    return jsonify([])


@bp.route('/scan', methods=['POST'])
def trigger_scan():
    """Trigger an immediate network scan."""
    global monitoring_service
    
    if monitoring_service:
        devices = monitoring_service.scan_network()
        return jsonify(devices)
    
    return jsonify({'error': 'Monitoring service not running'}), 400
