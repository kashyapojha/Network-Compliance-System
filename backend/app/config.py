"""Application configuration loaded from environment variables."""
import os
import secrets
import warnings
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Single source of truth: repository root `.env` (optional file)
if (PROJECT_ROOT / '.env').is_file():
    load_dotenv(PROJECT_ROOT / '.env', override=True)


def _require_secret(name: str, value: str | None) -> str:
    """Return secret value or generate a dev-only fallback with warning."""
    if value:
        return value
    if os.getenv('FLASK_ENV') == 'production' or os.getenv('DEBUG', '').lower() == 'false':
        raise RuntimeError(
            f'{name} must be set in environment or .env before running in production.'
        )
    generated = secrets.token_hex(32)
    warnings.warn(
        f'{name} not set — using a random dev-only value. Set {name} in .env at the repository root.',
        stacklevel=2,
    )
    return generated


class Config:
    SECRET_KEY = _require_secret('SECRET_KEY', os.getenv('SECRET_KEY'))
    JWT_SECRET_KEY = _require_secret('JWT_SECRET_KEY', os.getenv('JWT_SECRET_KEY'))
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', '5000'))

    _db_url = (os.getenv('DATABASE_URL') or '').strip()
    DATABASE_URL = _db_url or (
        'sqlite:///' + str(BACKEND_DIR / 'network_compliance.db').replace('\\', '/')
    )

    NETWORK_RANGE = (os.getenv('NETWORK_RANGE') or '').strip()
    POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '30'))

    _cert_dir = (os.getenv('CERTIFICATES_DIR') or '').strip()
    CERTIFICATES_DIR = _cert_dir or str(PROJECT_ROOT / 'certificates')

    CA_VALIDITY_DAYS = int(os.getenv('CA_VALIDITY_DAYS', '3650'))
    CERT_VALIDITY_DAYS = int(os.getenv('CERT_VALIDITY_DAYS', '365'))

    SMTP_HOST = os.getenv('SMTP_HOST', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '')

    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
    SOCKETIO_CORS_ORIGINS = os.getenv('SOCKETIO_CORS_ORIGINS', CORS_ORIGINS)

    BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')
