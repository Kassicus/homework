"""
Contract Management Platform - Flask Application Factory
"""
import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_name=None):
    """Application factory function"""
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app.config.from_object(f"app.config.{config_name.capitalize()}Config")

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Configure login manager
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # Setup logging
    setup_logging(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.clients import clients_bp
    from app.routes.contracts import contracts_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(contracts_bp, url_prefix="/contracts")
    app.register_blueprint(clients_bp, url_prefix="/clients")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")

    # Register main routes
    from app.routes.main import main_bp

    app.register_blueprint(main_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

        # Create initial admin user if none exists
        try:
            from app.models.user import User

            if not User.query.filter_by(is_admin=True).first():
                create_initial_admin(app)
        except Exception as e:
            app.logger.warning(f"Could not create initial admin user: {e}")
            # Continue without admin user creation

    return app


def setup_logging(app):
    """Configure application logging"""
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists("logs"):
            os.mkdir("logs")

        # File handler for application logs
        file_handler = RotatingFileHandler(
            "logs/contract-manager.log", maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        # Set application log level
        app.logger.setLevel(logging.INFO)
        app.logger.info("Contract Manager startup")


def create_initial_admin(app):
    """Create initial admin user during first startup"""
    import bcrypt

    from app.models.user import User

    try:
        # Hash password directly here to avoid circular import
        password = app.config.get("ADMIN_PASSWORD", "admin123")
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

        admin_user = User(
            username="admin",
            email=app.config.get("ADMIN_EMAIL", "admin@example.com"),
            password_hash=password_hash,
            is_active=True,
            is_admin=True,
        )
        db.session.add(admin_user)
        db.session.commit()
        app.logger.info("Initial admin user created successfully")
    except Exception as e:
        app.logger.error(f"Failed to create initial admin user: {e}")
        db.session.rollback()
