from flask import Blueprint, request, jsonify
import os
from ..services.monitoring_service import MonitoringService
from ..utils.network_utils import get_local_network_info, get_network_cidr
import threading

bp = Blueprint('monitoring', __name__)
monitoring_service = None
monitoring_thread = None


def _get_or_create_service(network_range=None):
    """Return monitoring service with the requested or auto-detected network range."""
    global monitoring_service
    network_range = (
        network_range
        or os.getenv('NETWORK_RANGE')
        or get_network_cidr()
    )
    if monitoring_service is None:
        monitoring_service = MonitoringService(network_range=network_range)
    else:
        monitoring_service.network_range = network_range
    return monitoring_service


@bp.route('/network-info', methods=['GET'])
def network_info():
    """Return auto-detected local network settings for the monitoring host."""
    info = get_local_network_info()
    return jsonify(info)


@bp.route('/start', methods=['POST'])
def start_monitoring():
    """Start the network monitoring service."""
    global monitoring_service, monitoring_thread

    data = request.get_json(silent=True) or {}
    network_range = data.get('network_range')

    if monitoring_service and monitoring_service.is_running:
        return jsonify({
            'message': 'Monitoring already running',
            'network_range': monitoring_service.network_range
        })

    monitoring_service = MonitoringService(network_range=network_range)
    monitoring_thread = threading.Thread(target=monitoring_service.start)
    monitoring_thread.daemon = True
    monitoring_thread.start()

    return jsonify({
        'message': 'Monitoring started',
        'network_range': monitoring_service.network_range
    })


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
            'network_range': monitoring_service.network_range,
            'devices_detected': len(monitoring_service.detected_devices),
            'alerts_generated': monitoring_service.alert_count
        })

    return jsonify({
        'running': False,
        'network_range': os.getenv('NETWORK_RANGE') or get_network_cidr()
    })


@bp.route('/devices', methods=['GET'])
def get_detected_devices():
    """Get currently detected devices from the last scan."""
    global monitoring_service

    if monitoring_service:
        return jsonify(monitoring_service.detected_devices)

    return jsonify([])


@bp.route('/scan', methods=['POST'])
def trigger_scan():
    """Trigger an immediate network scan and generate compliance alerts."""
    global monitoring_service

    data = request.get_json(silent=True) or {}
    network_range = data.get('network_range')

    service = _get_or_create_service(network_range)
    alerts_before = service.alert_count
    devices = service.scan_and_check()
    alerts_created = service.alert_count - alerts_before

    return jsonify({
        'message': 'Scan completed',
        'network_range': service.network_range,
        'devices_found': len(devices),
        'devices': service.detected_devices,
        'alerts_created': alerts_created
    })
