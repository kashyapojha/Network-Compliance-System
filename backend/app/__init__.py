from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from .database import init_db
from .config import Config
from .services.monitoring_service import set_monitoring_socketio

def create_app():
    """Application factory pattern."""
    app = Flask(__name__)

    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = Config.JWT_ACCESS_TOKEN_EXPIRES

    cors_origins = [o.strip() for o in Config.CORS_ORIGINS.split(',') if o.strip()]
    CORS(app, origins=cors_origins, supports_credentials=True)

    jwt = JWTManager(app)

    socket_origins = [o.strip() for o in Config.SOCKETIO_CORS_ORIGINS.split(',') if o.strip()]
    socketio = SocketIO(app, cors_allowed_origins=socket_origins or '*')
    set_monitoring_socketio(socketio)

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
