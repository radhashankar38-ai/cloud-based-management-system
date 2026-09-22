import os

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Load environment variables from .env if present
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-me-in-production')

    is_vercel = bool(os.environ.get('VERCEL'))
    _default_sqlite = '/tmp/cbms.db' if is_vercel else os.path.join(BASE_DIR, 'cbms.db')
    _db_url = os.environ.get(
        'DATABASE_URL', 'sqlite:///' + _default_sqlite
    )
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = '/tmp/uploads' if is_vercel else os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB per request

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # In production, serve over HTTPS and set SESSION_COOKIE_SECURE = True
