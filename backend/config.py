import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    APP_PASSWORD = os.environ.get('APP_PASSWORD')

    # Use platform-appropriate default path
    # In Docker: /app/data/inventory.db (set via DATABASE_PATH env var)
    # Elsewhere: ../data/inventory.db (relative to backend folder)
    _default_db = os.path.join(os.path.dirname(__file__), '..', 'data', 'inventory.db')

    DATABASE_PATH = os.environ.get('DATABASE_PATH', _default_db)
    APP_ENVIRONMENT = os.environ.get('APP_ENVIRONMENT', 'production')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    @classmethod
    def validate(cls):
        """Validate required configuration. Raises ValueError if invalid."""
        errors = []
        if not cls.SECRET_KEY:
            errors.append("SECRET_KEY environment variable is required")
        if not cls.APP_PASSWORD:
            errors.append("APP_PASSWORD environment variable is required")
        elif len(cls.APP_PASSWORD) < 8:
            errors.append("APP_PASSWORD must be at least 8 characters")

        if errors:
            raise ValueError("Configuration error(s): " + "; ".join(errors))
