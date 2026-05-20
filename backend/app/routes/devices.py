from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.device import Device
from ..models.certificate import Certificate
from ..utils.network_utils import get_local_network_info, normalize_mac
from ..utils.device_utils import compute_trust_score
from datetime import datetime

bp = Blueprint('devices', __name__)


@bp.route('/local-info', methods=['GET'])
def local_device_info():
    """Auto-detect this machine's hostname, IP, MAC, and network range."""
    return jsonify(get_local_network_info())


@bp.route('/', methods=['GET'])
def list_devices():
    """List all devices with optional filtering."""
    db: Session = next(get_db())
    try:
        query = db.query(Device)
        
        # Filter parameters
        if request.args.get('authorized'):
            query = query.filter(Device.is_authorized == (request.args.get('authorized') == 'true'))
        if request.args.get('quarantined'):
            query = query.filter(Device.is_quarantined == (request.args.get('quarantined') == 'true'))
        if request.args.get('department'):
            query = query.filter(Device.department == request.args.get('department'))
        if request.args.get('device_type'):
            query = query.filter(Device.device_type == request.args.get('device_type'))
        
        devices = query.all()
        return jsonify([{
            'id': d.id,
            'hostname': d.hostname,
            'mac_address': d.mac_address,
            'ip_address': d.ip_address,
            'device_type': d.device_type,
            'department': d.department,
            'os_fingerprint': d.os_fingerprint,
            'vendor': d.vendor,
            'trust_score': compute_trust_score(d),
            'is_authorized': d.is_authorized,
            'is_quarantined': d.is_quarantined,
            'vlan_assignment': d.vlan_assignment,
            'first_seen': d.first_seen.isoformat() if d.first_seen else None,
            'last_seen': d.last_seen.isoformat() if d.last_seen else None,
            'certificate_count': len(d.certificates)
        } for d in devices])
    finally:
        db.close()


@bp.route('/', methods=['POST'])
def register_device():
    """Register a new device."""
    db: Session = next(get_db())
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['hostname', 'mac_address', 'device_type', 'department']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if device already exists
        existing = db.query(Device).filter(
            (Device.hostname == data['hostname']) | 
            (Device.mac_address == data['mac_address'])
        ).first()
        
        if existing:
            return jsonify({'error': 'Device with this hostname or MAC already exists'}), 409
        
        # Create new device
        device = Device(
            hostname=data['hostname'],
            mac_address=normalize_mac(data['mac_address']),
            ip_address=data.get('ip_address'),
            device_type=data['device_type'],
            department=data['department'],
            os_fingerprint=data.get('os_fingerprint'),
            vendor=data.get('vendor'),
            is_authorized=data.get('is_authorized', False)
        )
        device.trust_score = compute_trust_score(device)

        db.add(device)
        db.commit()
        db.refresh(device)
        
        return jsonify({
            'id': device.id,
            'hostname': device.hostname,
            'mac_address': device.mac_address,
            'message': 'Device registered successfully. Certificate generation pending.'
        }), 201
    finally:
        db.close()


@bp.route('/<int:device_id>', methods=['GET'])
def get_device(device_id):
    """Get device details."""
    db: Session = next(get_db())
    try:
        device = db.query(Device).get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        return jsonify({
            'id': device.id,
            'hostname': device.hostname,
            'mac_address': device.mac_address,
            'ip_address': device.ip_address,
            'device_type': device.device_type,
            'department': device.department,
            'os_fingerprint': device.os_fingerprint,
            'vendor': device.vendor,
            'trust_score': device.trust_score,
            'is_authorized': device.is_authorized,
            'is_quarantined': device.is_quarantined,
            'vlan_assignment': device.vlan_assignment,
            'first_seen': device.first_seen.isoformat() if device.first_seen else None,
            'last_seen': device.last_seen.isoformat() if device.last_seen else None,
            'certificates': [{
                'id': c.id,
                'serial_number': c.serial_number,
                'issuer': c.issuer,
                'subject': c.subject,
                'not_valid_before': c.not_valid_before.isoformat() if c.not_valid_before else None,
                'not_valid_after': c.not_valid_after.isoformat() if c.not_valid_after else None,
                'is_revoked': c.is_revoked
            } for c in device.certificates]
        })
    finally:
        db.close()


@bp.route('/<int:device_id>/authorize', methods=['POST'])
def authorize_device(device_id):
    """Authorize a device (admin only)."""
    db: Session = next(get_db())
    try:
        device = db.query(Device).get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        device.is_authorized = True
        device.is_quarantined = False
        device.trust_score = compute_trust_score(device)
        db.commit()

        return jsonify({
            'message': 'Device authorized successfully',
            'trust_score': device.trust_score
        })
    finally:
        db.close()


@bp.route('/<int:device_id>/quarantine', methods=['POST'])
def quarantine_device(device_id):
    """Quarantine a device (admin only)."""
    db: Session = next(get_db())
    try:
        device = db.query(Device).get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        device.is_quarantined = True
        device.is_authorized = False
        device.trust_score = compute_trust_score(device)
        db.commit()

        return jsonify({
            'message': 'Device quarantined successfully',
            'trust_score': device.trust_score
        })
    finally:
        db.close()


@bp.route('/<int:device_id>/vlan', methods=['PUT'])
def assign_vlan(device_id):
    """Assign VLAN to a device."""
    db: Session = next(get_db())
    try:
        data = request.get_json()
        if 'vlan_id' not in data:
            return jsonify({'error': 'Missing vlan_id'}), 400
        
        device = db.query(Device).get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        device.vlan_assignment = data['vlan_id']
        db.commit()
        
        return jsonify({'message': 'VLAN assigned successfully'})
    finally:
        db.close()


@bp.route('/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Delete a device (admin only)."""
    db: Session = next(get_db())
    try:
        device = db.query(Device).get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        db.delete(device)
        db.commit()
        
        return jsonify({'message': 'Device deleted successfully'})
    finally:
        db.close()
