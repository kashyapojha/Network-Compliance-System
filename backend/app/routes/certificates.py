from flask import Blueprint, request, jsonify, send_file
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.certificate import Certificate
from ..models.device import Device
from ..services.certificate_service import CertificateService
import tempfile
import os
from datetime import datetime

bp = Blueprint('certificates', __name__)


@bp.route('/', methods=['GET'])
def list_certificates():
    """List all device certificates."""
    db: Session = next(get_db())
    try:
        certificates = db.query(Certificate).order_by(Certificate.created_at.desc()).all()
        return jsonify([{
            'id': c.id,
            'device_id': c.device_id,
            'device_hostname': c.device.hostname if c.device else None,
            'serial_number': c.serial_number,
            'issuer': c.issuer,
            'subject': c.subject,
            'not_valid_before': c.not_valid_before.isoformat() if c.not_valid_before else None,
            'not_valid_after': c.not_valid_after.isoformat() if c.not_valid_after else None,
            'is_revoked': c.is_revoked,
            'revoked_at': c.revoked_at.isoformat() if c.revoked_at else None,
            'revocation_reason': c.revocation_reason
        } for c in certificates])
    finally:
        db.close()


@bp.route('/generate/<int:device_id>', methods=['POST'])
def generate_certificate(device_id):
    """Generate and sign a certificate for a device."""
    db: Session = next(get_db())
    try:
        device = db.query(Device).get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Check if device already has valid certificate
        valid_cert = db.query(Certificate).filter(
            Certificate.device_id == device_id,
            Certificate.is_revoked == False
        ).first()
        
        if valid_cert:
            return jsonify({'error': 'Device already has a valid certificate'}), 400
        
        # Generate certificate
        cert_service = CertificateService()
        cert_data = cert_service.generate_device_certificate(device)
        
        # Save to database
        certificate = Certificate(
            device_id=device.id,
            serial_number=cert_data['serial_number'],
            certificate_pem=cert_data['certificate_pem'],
            private_key_pem=cert_data['private_key_pem'],
            issuer=cert_data['issuer'],
            subject=cert_data['subject'],
            not_valid_before=cert_data['not_valid_before'],
            not_valid_after=cert_data['not_valid_after']
        )
        
        db.add(certificate)
        
        # Authorize device
        device.is_authorized = True
        db.commit()
        
        return jsonify({
            'id': certificate.id,
            'serial_number': certificate.serial_number,
            'message': 'Certificate generated successfully',
            'not_valid_after': certificate.not_valid_after.isoformat()
        })
    finally:
        db.close()


@bp.route('/<int:cert_id>/download', methods=['GET'])
def download_certificate(cert_id):
    """Download certificate bundle (cert + key)."""
    db: Session = next(get_db())
    try:
        cert = db.query(Certificate).get(cert_id)
        if not cert:
            return jsonify({'error': 'Certificate not found'}), 404
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.p12', delete=False) as f:
            # In production, this should create a proper PKCS#12 bundle
            f.write(cert.certificate_pem)
            f.write('\n')
            f.write(cert.private_key_pem)
            temp_path = f.name
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=f"{cert.device.hostname}_bundle.pem",
            mimetype='application/x-pem-file'
        )
    finally:
        db.close()


@bp.route('/<int:cert_id>/revoke', methods=['POST'])
def revoke_certificate(cert_id):
    """Revoke a certificate."""
    db: Session = next(get_db())
    try:
        data = request.get_json()
        cert = db.query(Certificate).get(cert_id)
        if not cert:
            return jsonify({'error': 'Certificate not found'}), 404
        
        cert.is_revoked = True
        cert.revoked_at = datetime.utcnow()
        cert.revocation_reason = data.get('reason', 'Admin revocation')
        
        # Deauthorize device
        cert.device.is_authorized = False
        
        db.commit()
        
        return jsonify({'message': 'Certificate revoked successfully'})
    finally:
        db.close()


@bp.route('/device/<int:device_id>', methods=['GET'])
def get_device_certificates(device_id):
    """Get all certificates for a device."""
    db: Session = next(get_db())
    try:
        certificates = db.query(Certificate).filter(
            Certificate.device_id == device_id
        ).all()
        
        return jsonify([{
            'id': c.id,
            'serial_number': c.serial_number,
            'issuer': c.issuer,
            'subject': c.subject,
            'not_valid_before': c.not_valid_before.isoformat() if c.not_valid_before else None,
            'not_valid_after': c.not_valid_after.isoformat() if c.not_valid_after else None,
            'is_revoked': c.is_revoked,
            'revoked_at': c.revoked_at.isoformat() if c.revoked_at else None,
            'revocation_reason': c.revocation_reason
        } for c in certificates])
    finally:
        db.close()


@bp.route('/ca/info', methods=['GET'])
def get_ca_info():
    """Get CA certificate information."""
    cert_service = CertificateService()
    ca_info = cert_service.get_ca_info()
    return jsonify(ca_info)
