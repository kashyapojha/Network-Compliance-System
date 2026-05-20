from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.admin import Admin, UserRole
from ..utils.auth import hash_password, verify_password
from datetime import datetime

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['POST'])
def register():
    """Register a new admin user."""
    db: Session = next(get_db())
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user exists
        existing = db.query(Admin).filter(
            (Admin.username == data['username']) | 
            (Admin.email == data['email'])
        ).first()
        
        if existing:
            return jsonify({'error': 'Username or email already exists'}), 409
        
        # Parse role safely
        role_str = data.get('role', 'user')
        try:
            role_enum = UserRole(role_str)
        except ValueError:
            role_enum = UserRole.USER

        # Create admin
        admin = Admin(
            username=data['username'],
            email=data['email'],
            hashed_password=hash_password(data['password']),
            role=role_enum
        )
        
        db.add(admin)
        db.commit()
        
        return jsonify({
            'id': admin.id,
            'username': admin.username,
            'email': admin.email,
            'role': admin.role.value
        }), 201
    finally:
        db.close()


@bp.route('/login', methods=['POST'])
def login():
    """Login and get JWT token."""
    db: Session = next(get_db())
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Missing username or password'}), 400
        
        admin = db.query(Admin).filter(Admin.username == data['username']).first()
        
        if not admin or not verify_password(data['password'], admin.hashed_password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not admin.is_active:
            return jsonify({'error': 'Account is inactive'}), 403
        
        # Update last login
        admin.last_login = datetime.utcnow()
        db.commit()
        
        # Generate token
        access_token = create_access_token(identity=str(admin.id))
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': admin.id,
                'username': admin.username,
                'email': admin.email,
                'role': admin.role.value
            }
        })
    finally:
        db.close()


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info."""
    db: Session = next(get_db())
    try:
        admin_id = int(get_jwt_identity())
        admin = db.query(Admin).get(admin_id)
        
        if not admin:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'id': admin.id,
            'username': admin.username,
            'email': admin.email,
            'role': admin.role.value,
            'is_active': admin.is_active,
            'last_login': admin.last_login.isoformat() if admin.last_login else None
        })
    finally:
        db.close()
