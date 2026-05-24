from flask import Blueprint, request, jsonify
import os
from ..services.monitoring_service import MonitoringService
from ..utils.network_utils import get_local_network_info, get_network_cidr
import threading
import logging

log = logging.getLogger(__name__)

bp = Blueprint('monitoring', __name__)
monitoring_service = None
monitoring_thread = None


def _get_or_create_service(network_range=None):
    """Return monitoring service with the requested or auto-detected network range.

    FIX: Never mutate a running service's network_range mid-scan — that causes
    a race condition with the background loop. Instead, always create a fresh
    one-shot service for manual scans so the background instance is untouched.
    """
    resolved_range = (
        network_range
        or os.getenv('NETWORK_RANGE')
        or get_network_cidr()
    )
    # Always return a fresh instance for one-shot scans.
    # The background monitoring_service (started via /start) is separate.
    return MonitoringService(network_range=resolved_range)


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


@bp.route('/scan-history', methods=['GET'])
def get_scan_history():
    """Return last 20 scan results for the Recent Scan Activity panel."""
    global monitoring_service
    service = monitoring_service or _get_or_create_service()
    return jsonify(service.get_scan_history())


@bp.route('/scan', methods=['POST'])
def trigger_scan():
    """Trigger an immediate network scan and generate compliance alerts.

    FIX: Wrapped scan_and_check() in a try/except so permission errors,
    OS errors, and unexpected exceptions return a structured JSON error
    instead of an unhandled 500 — which is what was causing the frontend
    to show 'Network scan failed. Is the backend running as Administrator?'
    even when the real problem was something else entirely.
    """
    data = request.get_json(silent=True) or {}
    network_range = data.get('network_range')

    service = _get_or_create_service(network_range)
    alerts_before = service.alert_count

    try:
        devices = service.scan_and_check()
    except PermissionError:
        log.error("Scan failed: insufficient privileges (run backend as Administrator)")
        return jsonify({
            'error': 'permission_denied',
            'message': (
                'Network scan requires Administrator privileges. '
                'Right-click your terminal and choose "Run as Administrator", '
                'then restart the backend.'
            ),
            'devices_found': 0,
            'alerts_created': 0,
        }), 403
    except OSError as e:
        log.error(f"Scan failed with OS error: {e}")
        return jsonify({
            'error': 'os_error',
            'message': f'OS error during scan: {e}. The ARP fallback may also be unavailable.',
            'devices_found': 0,
            'alerts_created': 0,
        }), 500
    except Exception as e:
        log.exception(f"Unexpected scan error: {e}")
        return jsonify({
            'error': 'scan_failed',
            'message': f'Scan failed unexpectedly: {str(e)}',
            'devices_found': 0,
            'alerts_created': 0,
        }), 500

    alerts_created = service.alert_count - alerts_before

    return jsonify({
        'message': 'Scan completed',
        'network_range': service.network_range,
        'devices_found': len(devices),
        'devices': service.detected_devices,
        'alerts_created': alerts_created
    })