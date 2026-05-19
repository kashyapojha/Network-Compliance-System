from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from .database import init_db
import os

def create_app():
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # 1 hour
    
    # Enable CORS
    CORS(app)
    
    # Initialize SocketIO for WebSocket support
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Initialize database
    init_db()
    
    # Register blueprints
    from .routes import devices, certificates, auth, alerts, monitoring, compliance
    
    app.register_blueprint(devices.bp, url_prefix='/api/devices')
    app.register_blueprint(certificates.bp, url_prefix='/api/certificates')
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(alerts.bp, url_prefix='/api/alerts')
    app.register_blueprint(monitoring.bp, url_prefix='/api/monitoring')
    app.register_blueprint(compliance.bp, url_prefix='/api/compliance')
    
    return app, socketio
