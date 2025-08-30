"""
Configuration classes for Contract Management Platform
"""
from datetime import timedelta
import os


class Config:
    """Base configuration class"""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # File upload configuration
    MAX_CONTENT_LENGTH = int(
        os.environ.get("MAX_UPLOAD_SIZE", 131072000)
    )  # 125MB default
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))
    ALLOWED_EXTENSIONS = os.environ.get(
        "ALLOWED_EXTENSIONS", "pdf,docx,doc,txt,rtf"
    ).split(",")

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True

    # CSRF protection
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # Admin credentials
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///contracts.db"

    # Development-specific settings
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or "sqlite:////var/lib/contract-manager/contracts.db"
    )
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "/var/lib/contract-manager/uploads")

    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    WTF_CSRF_ENABLED = True

    # Production logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING")


class TestingConfig(Config):
    """Testing configuration"""

    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False

    # Test-specific settings
    UPLOAD_FOLDER = "test_uploads"
    LOG_LEVEL = "DEBUG"


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
