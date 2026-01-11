import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
    APP_PASSWORD = os.environ.get('APP_PASSWORD', 'home123')

    # Use platform-appropriate default path
    # In Docker: /app/data/inventory.db (set via DATABASE_PATH env var)
    # Elsewhere: ../data/inventory.db (relative to backend folder)
    _default_db = os.path.join(os.path.dirname(__file__), '..', 'data', 'inventory.db')

    DATABASE_PATH = os.environ.get('DATABASE_PATH', _default_db)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
